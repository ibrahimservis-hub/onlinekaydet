/* ServisPlus panel eki: karanlık/açık tema, sürükle-bırak menü, Site Yönetimi (aç/kapat, SEO, 301/404, iyzico, pazaryeri, panelden sipariş). index.html'e tek satır eklenir. */
(function () {
  'use strict';
  var SITE = window.SP_SITE_API || 'https://servisplus.net.tr/api/panel.php';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var LS = { get: function (k, d) { try { var v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } }, set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { } } };

  /* ---------- stil ---------- */
  var css = '' +
    'body.spx-tech [role=tablist]{display:flex!important;justify-content:flex-start!important;flex-wrap:nowrap;gap:2px;overflow-x:auto;height:auto!important;scrollbar-width:none;-webkit-overflow-scrolling:touch}' +
    'body.spx-tech [role=tablist]::-webkit-scrollbar{display:none}' +
    'body.spx-tech [role=tablist]>[role=tab],body.spx-tech [role=tablist]>button{flex:1 0 auto!important;white-space:nowrap!important;width:auto!important;position:static!important;padding:7px 12px!important;font-size:13px!important;text-align:center}' +
    '#spx-theme{position:fixed;right:12px;top:8px;bottom:auto;z-index:9998;width:34px;height:34px;border-radius:8px;border:1px solid #cbd5e1;background:#fff;color:#0f172a;font-size:16px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.15)}body.spx-tech #spx-theme{display:none}' +
    '#spx-lang{position:relative;z-index:9999;flex:none}#spx-lang>button{border:1px solid #cbd5e1;background:#fff;color:#0f172a;border-radius:8px;height:32px;padding:0 8px;font:700 11px/1 Inter,system-ui,sans-serif;cursor:pointer}#spx-lang .m{display:none;position:absolute;right:0;top:40px;background:#fff;border:1px solid #cbd5e1;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.18);padding:4px;min-width:120px}#spx-lang.open .m{display:block}#spx-lang .m button{display:block;width:100%;text-align:left;border:0;background:none;padding:9px 12px;border-radius:6px;font:600 13px Inter,system-ui,sans-serif;color:#0f172a;cursor:pointer}#spx-lang .m button.on{background:#e0ecff;color:#1155cc}.spx-dark #spx-lang>button,.spx-dark #spx-lang .m{background:#162033;color:#e2e8f0;border-color:#2b3a52}.spx-dark #spx-lang .m button{color:#e2e8f0}' +
    '@media(min-width:1024px){body.spx-tech nav.fixed.bottom-0{top:56px!important;bottom:0!important;right:auto!important;left:0!important;width:256px!important;border-top:0!important;border-right:1px solid #e2e8f0!important;padding:14px 12px!important;overflow-y:auto;background:#fff!important}' +
    'body.spx-tech nav.fixed.bottom-0>div{display:flex!important;flex-direction:column!important;max-width:none!important;gap:4px}' +
    'body.spx-tech nav.fixed.bottom-0 a[data-testid^=tab-]{flex-direction:row!important;justify-content:flex-start!important;gap:12px!important;padding:11px 14px!important;font-size:14px!important;font-weight:600;border-radius:10px;position:relative}' +
    'body.spx-tech nav.fixed.bottom-0 a[data-testid^=tab-]:hover{background:#f1f5f9}' +
    'body.spx-tech nav.fixed.bottom-0 a[data-testid^=tab-].text-blue-600,body.spx-tech nav.fixed.bottom-0 a[data-testid^=tab-][aria-current]{background:#eff6ff}' +
    'body.spx-tech nav.fixed.bottom-0 .spx-trb{right:12px!important;left:auto!important;top:50%!important;transform:translateY(-50%)}' +
    'body.spx-tech main.flex-1{margin-left:256px!important;margin-right:0!important;max-width:none!important;width:calc(100% - 256px)!important;box-sizing:border-box;padding:28px 32px!important}' +
    'body.spx-tech header.sticky{padding-left:24px!important;padding-right:24px!important}' +
    'body.spx-tech #spx-trov>*,body.spx-tech #spx-faqov>*{max-width:860px;margin-left:auto;margin-right:auto;width:100%}' +
    'body.spx-tech #spx-trov,body.spx-tech #spx-faqov,body.spx-tech #spx-cev{left:256px!important;top:56px!important}}' +
    'body>.skiptranslate,.goog-te-banner-frame{display:none!important}body{top:0!important}' +
    '#spx-tabs{display:none!important}#spx-ov #spx-menu{display:none}@media(min-width:1024px){#spx-ov{left:256px!important}}@media(max-width:1023px){#spx-ov #spx-menu{display:inline-block}}' +
    '[data-spx-own] a{text-decoration:none}[data-spx-own] .spx-sub a{display:block;padding:5px 12px;border-radius:6px;font-size:13px;color:#475569}[data-spx-own] .spx-sub a.on{background:#eff6ff;color:#1d4ed8;font-weight:600}[data-spx-own] .spx-sub{margin:2px 0 4px 20px;padding-left:12px;border-left:1px solid #e2e8f0}[data-spx-own] a.spx-it{display:flex;align-items:center;gap:12px;padding:7px 12px;border-radius:6px;font-size:14px;font-weight:500;color:#475569;border:1px solid transparent;cursor:pointer}[data-spx-own] a.spx-it:hover{background:#f8fafc;color:#0f172a}[data-spx-own] a.spx-it.on{background:#eff6ff;color:#1d4ed8;border-color:#dbeafe}[data-spx-own] a.spx-it svg{width:16px;height:16px;flex:none}[data-spx-own] a.spx-it span.l{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}[data-spx-own] .spx-gt{padding:0 12px;margin:14px 0 6px;font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#94a3b8}[data-spx-own] .spx-bd{min-width:20px;height:20px;padding:0 6px;border-radius:99px;font-size:11px;font-weight:700;color:#fff;background:#ef4444;display:inline-flex;align-items:center;justify-content:center}' +
    '.spx-dark [data-spx-own] a.spx-it{color:#cbd5e1}.spx-dark [data-spx-own] a.spx-it:hover{background:#1d2a42;color:#fff}.spx-dark [data-spx-own] a.spx-it.on,.spx-dark [data-spx-own] .spx-sub a.on{background:#17325a;color:#93c5fd;border-color:#1e3a6e}.spx-dark [data-spx-own] .spx-sub a{color:#cbd5e1}.spx-dark [data-spx-own] .spx-sub{border-color:#2b3a52}' +
    '#spx-ov{position:fixed;inset:0;z-index:40;background:#f1f5f9;color:#0f172a;display:none;flex-direction:column;font:14px/1.45 Inter,system-ui,sans-serif}#spx-ov.on{display:flex}' +
    '#spx-ov header{display:flex;align-items:center;gap:12px;padding:12px 18px;background:#fff;border-bottom:1px solid #e2e8f0}#spx-ov header h2{margin:0;font-size:17px;flex:1}' +
    '#spx-tabs{display:flex;gap:4px;padding:8px 18px 0;background:#fff;border-bottom:1px solid #e2e8f0;overflow-x:auto}' +
    '#spx-tabs button{border:0;background:none;padding:9px 14px;border-bottom:2px solid transparent;color:#475569;font-weight:600;cursor:pointer;white-space:nowrap}#spx-tabs button.on{color:#1155cc;border-color:#1155cc}' +
    '#spx-body{flex:1;overflow:auto;padding:18px}.spx-card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;margin-bottom:14px}' +
    '#spx-ov table{width:100%;border-collapse:collapse;font-size:13px}#spx-ov th,#spx-ov td{text-align:left;padding:8px 10px;border-bottom:1px solid #eef2f6;vertical-align:top}#spx-ov th{color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:.06em}' +
    '#spx-ov input,#spx-ov select,#spx-ov textarea{border:1px solid #cbd5e1;border-radius:6px;padding:7px 9px;font:inherit;background:#fff;color:inherit;max-width:100%}#spx-ov textarea{width:100%}' +
    '.spx-b{border:1px solid #cbd5e1;background:#fff;border-radius:6px;padding:6px 12px;font-weight:600;cursor:pointer;color:#0f172a}.spx-b.p{background:#1155cc;border-color:#1155cc;color:#fff}.spx-b.d{color:#b91c1c;border-color:#fecaca}' +
    '.spx-row{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #eef2f6}.spx-row:last-child{border:0}.spx-row .t{flex:1}.spx-row small{display:block;color:#64748b}' +
    '.spx-sw{position:relative;width:44px;height:24px;flex:none}.spx-sw input{opacity:0;width:100%;height:100%;position:absolute;margin:0;cursor:pointer;z-index:2}.spx-sw i{position:absolute;inset:0;background:#cbd5e1;border-radius:99px;transition:.15s}.spx-sw i:after{content:"";position:absolute;left:3px;top:3px;width:18px;height:18px;border-radius:50%;background:#fff;transition:.15s}.spx-sw input:checked+i{background:#16a34a}.spx-sw input:checked+i:after{left:23px}' +
    '.spx-g{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}.spx-g label{display:block;font-size:12px;color:#64748b}.spx-g input,.spx-g select{width:100%;margin-top:3px}.spx-stat{font-size:26px;font-weight:700}.spx-pill{display:inline-block;padding:2px 8px;border-radius:99px;background:#e0ecff;color:#1155cc;font-size:12px;font-weight:600}' +
    '#spx-toast{position:fixed;left:50%;top:72px;max-width:92vw;text-align:center;transform:translateX(-50%);background:#0f172a;color:#fff;padding:10px 18px;border-radius:8px;z-index:10000;display:none}' +
    /* koyu tema: panelin Tailwind sınıflarını ezer */
    'html.spx-dark{color-scheme:dark}html.spx-dark body{background:#0b1220!important;color:#e2e8f0}' +
    '.spx-dark .bg-white,.spx-dark .bg-card,.spx-dark #spx-ov header,.spx-dark #spx-tabs,.spx-dark .spx-card,.spx-dark #spx-theme,.spx-dark .spx-b{background:#162033!important;color:#e2e8f0}' +
    '.spx-dark .bg-slate-50,.spx-dark .bg-gray-50,.spx-dark .bg-slate-100,.spx-dark #spx-ov{background:#0f192b!important}' +
    '.spx-dark .bg-slate-200{background:#243247!important}' +
    '.spx-dark .text-slate-900,.spx-dark .text-slate-800,.spx-dark .text-foreground,.spx-dark .text-black{color:#f1f5f9!important}.spx-dark .text-slate-700,.spx-dark .text-slate-600{color:#cbd5e1!important}.spx-dark .text-slate-500,.spx-dark .text-slate-400{color:#94a3b8!important}' +
    '.spx-dark .border-slate-200,.spx-dark .border-slate-100,.spx-dark .border-slate-300,.spx-dark .border,.spx-dark .border-b,.spx-dark .border-t,.spx-dark .border-r,.spx-dark .divide-y>*{border-color:#2b3a52!important}' +
    '.spx-dark .bg-blue-50,.spx-dark .bg-indigo-50{background:#17325a!important}.spx-dark .text-blue-700,.spx-dark .text-blue-600{color:#93c5fd!important}' +
    '.spx-dark .bg-green-50,.spx-dark .bg-emerald-50{background:#12341f!important}.spx-dark .bg-red-50,.spx-dark .bg-rose-50{background:#3a1717!important}.spx-dark .bg-amber-50,.spx-dark .bg-yellow-50,.spx-dark .bg-orange-50{background:#3a2c0f!important}' +
    '.spx-dark .hover\\:bg-slate-50:hover,.spx-dark .hover\\:bg-slate-100:hover{background:#1d2a42!important}' +
    '.spx-dark input,.spx-dark select,.spx-dark textarea{background:#0f192b!important;color:#e2e8f0!important;border-color:#2b3a52!important}' +
    '.spx-dark #spx-ov th,.spx-dark #spx-ov td{border-color:#2b3a52}.spx-dark .spx-row{border-color:#2b3a52}.spx-dark .spx-pill{background:#17325a;color:#93c5fd}' +
    '.spx-dark table th{background:transparent!important}.spx-dark .recharts-text{fill:#cbd5e1}.spx-dark img[src*="logo"]{filter:brightness(1.15)}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  /* ---------- tema ---------- */
  var root = document.documentElement;
  function setTheme(d) { root.classList.toggle('spx-dark', d); LS.set('spx-theme', d ? 'dark' : 'light'); if (btn) btn.textContent = d ? '☀️' : '🌙'; }
  var btn = document.createElement('button'); btn.id = 'spx-theme'; btn.type = 'button'; btn.title = 'Karanlık / açık tema'; btn.setAttribute('aria-label', 'Tema değiştir');
  btn.onclick = function () { setTheme(!root.classList.contains('spx-dark')); };
  (function () { var v = LS.get('spx-theme', null); var d = v ? v === 'dark' : false; root.classList.toggle('spx-dark', d); document.addEventListener('DOMContentLoaded', function () { document.body.appendChild(btn); btn.textContent = d ? '☀️' : '🌙'; }); if (document.body) { document.body.appendChild(btn); btn.textContent = d ? '☀️' : '🌙'; } })();


  /* ---------- usta ekranı: üst dil butonları ---------- */
  var LG = [['tr', 'TR'], ['en', 'EN'], ['de', 'DE'], ['ar', 'AR'], ['ru', 'RU'], ['fr', 'FR']];
  function curLg() { var m = document.cookie.match(/googtrans=\/[a-zA-Z-]+\/([a-zA-Z-]+)/); return m ? m[1] : 'tr'; }
  function setLg(c) {
    var h = location.hostname, p = h.split('.'), r = p.length > 2 ? '.' + p.slice(-2).join('.') : h;
    var v = c === 'tr' ? '' : '/tr/' + c, e = c === 'tr' ? 'Thu, 01 Jan 1970 00:00:00 GMT' : new Date(Date.now() + 365 * 864e5).toUTCString();
    [null, h, r].forEach(function (d) { document.cookie = 'googtrans=' + v + ';expires=' + e + ';path=/' + (d ? ';domain=' + d : ''); });
    location.reload();
  }
  function loadGT() {
    if (curLg() === 'tr' || window.__spxGt) return; window.__spxGt = 1;
    var d = document.createElement('div'); d.id = 'spx_gt'; d.style.display = 'none'; document.body.appendChild(d);
    window.spxGtInit = function () { try { new google.translate.TranslateElement({ pageLanguage: 'tr', includedLanguages: 'en,de,ar,ru,fr', autoDisplay: false }, 'spx_gt'); } catch (e) { } };
    var s = document.createElement('script'); s.src = 'https://translate.google.com/translate_a/element.js?cb=spxGtInit'; s.async = true; document.head.appendChild(s);
  }
  function techBar() {
    var tech = /^\/tech(\/|$)/.test(location.pathname); document.body.classList.toggle('spx-tech', tech);
    var bar = document.getElementById('spx-lang'), hd = tech && document.querySelector('header.sticky');
    if (!tech || !hd) { if (bar) bar.remove(); return; }
    if (bar) return;
    bar = document.createElement('div'); bar.id = 'spx-lang'; bar.className = 'notranslate'; bar.setAttribute('translate', 'no');
    var c = curLg();
    var N = { tr: 'Türkçe', en: 'English', de: 'Deutsch', ar: 'العربية', ru: 'Русский', fr: 'Français' };
    bar.innerHTML = '<button type="button" data-o="1">🌐 ' + c.toUpperCase() + ' ▾</button><div class="m">' + LG.map(function (l) { return '<button type="button" data-l="' + l[0] + '"' + (l[0] === c ? ' class="on"' : '') + '>' + N[l[0]] + '</button>'; }).join('') + '</div>';
    bar.onclick = function (e) { var b = e.target.closest('button'); if (!b) return; if (b.getAttribute('data-o')) bar.classList.toggle('open'); else if (b.getAttribute('data-l')) setLg(b.getAttribute('data-l')); };
    document.addEventListener('click', function (e) { if (!bar.contains(e.target)) bar.classList.remove('open'); });
    var tg = hd.querySelector('[data-testid=theme-toggle]'); if (tg && tg.parentNode) tg.parentNode.insertBefore(bar, tg); else hd.appendChild(bar); return;
    hd.parentNode.insertBefore(bar, hd.nextSibling);
  }
  setInterval(techBar, 700); document.addEventListener('DOMContentLoaded', function () { techBar(); loadGT(); });

  /* ---------- usta: eski dil satırını kaldır + bildirim aç düğmesi ---------- */
  function killOldLang() {
    if (!document.body.classList.contains('spx-tech')) return;
    var m = document.querySelector('main'); if (!m) return;
    var kids = m.querySelectorAll(':scope > div');
    for (var i = 0; i < kids.length && i < 3; i++) {
      var t = kids[i].textContent || '';
      if (/Türkçe/.test(t) && /English/.test(t) && kids[i].querySelectorAll('button').length <= 6) kids[i].style.display = 'none';
    }
  }
  function hideMail() {
    if (!document.body.classList.contains('spx-tech')) return;
    var hd = document.querySelector('header.sticky'); if (!hd) return;
    var els = hd.querySelectorAll('*');
    for (var i = 0; i < els.length; i++) { var e = els[i]; if (e.children.length === 0 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((e.textContent || '').trim())) e.style.display = 'none'; }
  }
  function b64u(s) { var p = '='.repeat((4 - s.length % 4) % 4), b = (s + p).replace(/-/g, '+').replace(/_/g, '/'), r = atob(b), o = new Uint8Array(r.length); for (var i = 0; i < r.length; i++) o[i] = r.charCodeAt(i); return o; }
  function pcall(m, p, b) {
    var o = { method: m, headers: { Authorization: 'Bearer ' + LS.get('token', ''), 'Content-Type': 'application/json' } }; if (b) o.body = JSON.stringify(b);
    return fetch(location.origin + '/api' + p, o).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) throw new Error((j && typeof j.detail === 'string' && j.detail) || 'Sunucu hatası ' + r.status); return j; }); });
  }
  function pushSub(askPerm) {
    if (!('serviceWorker' in navigator) || !('PushManager' in window) || !window.Notification) return Promise.reject(new Error('Bu tarayıcı bildirimi desteklemiyor. iPhone için uygulamayı "Ana Ekrana Ekle" yapıp oradan açın.'));
    var p = Notification.permission === 'granted' ? Promise.resolve('granted') : (askPerm ? Notification.requestPermission() : Promise.resolve(Notification.permission));
    return p.then(function (perm) {
      if (perm !== 'granted') throw new Error('Bildirim izni verilmedi. Tarayıcı adres çubuğundaki kilit simgesinden "Bildirimler"i açın.');
      return navigator.serviceWorker.register('/spx-sw.js', { scope: '/spx-push/' });
    }).then(function (reg) { return navigator.serviceWorker.ready.then(function () { return reg; }); })
      .then(function (reg) { return reg.pushManager.getSubscription().then(function (sub) { if (sub) return sub; return pcall('GET', '/push/public-key').then(function (k) { return reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64u(k.key) }); }); }); })
      .then(function (sub) { return pcall('POST', '/push/subscribe', JSON.parse(JSON.stringify(sub))); });
  }
  function bellBtn() {
    if (!document.body.classList.contains('spx-tech')) { var o = document.getElementById('spx-bell'); if (o) o.remove(); return; }
    var hd = document.querySelector('header.sticky'); if (!hd || document.getElementById('spx-bell')) return;
    var b = document.createElement('button'); b.id = 'spx-bell'; b.type = 'button'; b.title = 'Bildirimleri aç / test et'; b.className = 'notranslate';
    var on = window.Notification && Notification.permission === 'granted';
    b.textContent = on ? '🔔' : '🔕'; b.style.cssText = 'border:1px solid #cbd5e1;background:#fff;border-radius:8px;height:32px;width:34px;font-size:15px;cursor:pointer;flex:none;margin-right:4px';
    b.onclick = function () {
      toast('Bildirim hazırlanıyor…');
      pushSub(true).then(function () { b.textContent = '🔔'; return pcall('POST', '/push/test'); }).then(function (r) { toast(r.sent ? 'Bildirimler açık ✔ — test bildirimi gönderildi' : 'Kayıt yapıldı ama test iletilemedi (sunucu push gönderemiyor)'); }).catch(function (e) { toast(e.message || 'Bildirim açılamadı'); });
    };
    var lg = document.getElementById('spx-lang'); if (lg && lg.parentNode) lg.parentNode.insertBefore(b, lg); else hd.appendChild(b);
    if (on) pushSub(false).catch(function () { });
  }
  setInterval(function () { killOldLang(); bellBtn(); hideMail(); }, 700);

  /* ---------- usta: yeni iş / durum değişikliği 12 sn içinde otomatik görünsün ---------- */
  var JSIG = null, JBUSY = false;
  function jobPoll() {
    if (JBUSY || document.hidden || !/^\/tech\/?$/.test(location.pathname) || !LS.get('token', '')) return;
    JBUSY = true;
    pcall('GET', '/jobs').then(function (rows) {
      var sig = (Array.isArray(rows) ? rows : []).map(function (r) { return r.id + ':' + r.status + ':' + (r.updated_at || ''); }).join('|');
      if (JSIG !== null && sig !== JSIG) {
        try { navigator.vibrate && navigator.vibrate([200, 100, 200]); } catch (e) { }
        toast('Görev listesi güncellendi');
        var ae = document.activeElement; if (!ae || !/^(INPUT|TEXTAREA|SELECT)$/.test(ae.tagName)) { JSIG = sig; setTimeout(function () { location.reload(); }, 600); return; }
      }
      JSIG = sig;
    }).catch(function () { }).then(function () { JBUSY = false; });
  }
  setInterval(jobPoll, 12000); document.addEventListener('visibilitychange', function () { if (!document.hidden) jobPoll(); });

  /* ---------- usta iş ekranı: Kaydet / Tamamla / QR Etiket çubuğu içeriğin üstüne binmesin ---------- */
  function fixActionBar() {
    if (!/^\/tech\/jobs\//.test(location.pathname)) return;
    var btns = document.querySelectorAll('main button, main a, #root button');
    for (var i = 0; i < btns.length; i++) {
      var t = (btns[i].textContent || '').trim();
      if (!/^(Kaydet|Tamamla|QR Etiket)$/.test(t)) continue;
      var el = btns[i];
      for (var d = 0; el && d < 6 && el !== document.body; d++, el = el.parentElement) {
        var p = getComputedStyle(el).position;
        if (p === 'fixed' || p === 'sticky') { el.style.setProperty('position', 'static', 'important'); el.style.setProperty('bottom', 'auto', 'important'); el.style.setProperty('box-shadow', 'none', 'important'); el.style.setProperty('margin', '12px 0', 'important'); el.style.setProperty('transform', 'none', 'important'); }
      }
    }
    /* iş tamamlanmışsa (Tamamla düğmesi yoksa) QR Etiket düğmesi kalkar */
    var hasDone = false, qrs = [];
    for (var j = 0; j < btns.length; j++) { var tt = (btns[j].textContent || '').trim(); if (tt === 'Tamamla') hasDone = true; else if (tt === 'QR Etiket') qrs.push(btns[j]); }
    for (var k = 0; k < qrs.length; k++) { if (!hasDone) qrs[k].style.setProperty('display', 'none', 'important'); else qrs[k].style.removeProperty('display'); }
    var mn = document.querySelector('main'); if (mn) mn.style.setProperty('padding-bottom', '110px', 'important');
  }
  setInterval(fixActionBar, 500);

  /* ---------- usta: borç oranı ana ekrandan kalkar, Bakiyem sayfasında oran + IBAN görünür ---------- */
  var PAY = null, PAYBUSY = false;
  function hideRate() {
    var els = document.querySelectorAll('main div, main p, main span');
    for (var i = 0; i < els.length; i++) {
      var e = els[i];
      if (/^Şirkete borç oranınız/.test((e.textContent || '').trim()) && !e.querySelector('div,p') && !e.closest('#spx-pay')) { e.style.setProperty('display', 'none', 'important'); }
    }
    /* ana ekrandaki "Borç ₺…" kartı usta girişinde görünmesin (borç sadece Bakiyem sayfasında) */
    var cd = document.querySelectorAll('main .uppercase');
    for (var j = 0; j < cd.length; j++) {
      if ((cd[j].textContent || '').trim() === 'Borç') { var card = cd[j].closest('[class*="border"]') || cd[j].parentElement.parentElement; if (card && card.tagName !== 'MAIN') card.style.setProperty('display', 'none', 'important'); }
    }
  }
  function payCard() {
    if (!document.body.classList.contains('spx-tech')) return;
    if (/^\/tech\/?$/.test(location.pathname)) hideRate();
    var onBal = /^\/tech\/balance/.test(location.pathname), ex = document.getElementById('spx-pay');
    if (!onBal) { if (ex) ex.remove(); return; }
    var mn = document.querySelector('main'); if (!mn || ex) return;
    if (!PAY) {
      if (PAYBUSY) return; PAYBUSY = true;
      pcall('GET', '/tech/pay-info').then(function (r) { PAY = r; }).catch(function () { PAY = { accounts: [], commission_percent: null }; }).then(function () { PAYBUSY = false; });
      return;
    }
    var h = '<div id="spx-pay" class="notranslate" style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:14px;margin-bottom:14px">';
    if (PAY.commission_percent != null) h += '<div style="font-size:12px;color:#64748b;font-weight:600;letter-spacing:.04em;text-transform:uppercase">Şirkete borç oranınız</div><div style="font-size:22px;font-weight:800;color:#c2410c;margin:2px 0 10px">%' + esc(String(PAY.commission_percent)) + '</div>';
    h += '<div style="font-size:12px;color:#64748b;font-weight:600;letter-spacing:.04em;text-transform:uppercase;margin-bottom:6px">Şirket ödeme (IBAN) bilgileri</div>';
    if (!PAY.accounts || !PAY.accounts.length) h += '<div style="font-size:13px;color:#64748b">Henüz IBAN bilgisi tanımlanmamış. Yönetici panelinde Mağaza ayarlarından banka hesabı ekleyin.</div>';
    (PAY.accounts || []).forEach(function (a) {
      var ib = String(a.iban || '').replace(/(.{4})/g, '$1 ').trim();
      h += '<div style="background:#f6f7f9;border-radius:10px;padding:10px 12px;margin-bottom:8px"><div style="font-weight:700;color:#0a1f44;font-size:14px">' + esc(a.bank || 'Banka') + '</div>' + (a.holder ? '<div style="font-size:13px;color:#475569">' + esc(a.holder) + '</div>' : '') + '<div style="font:700 14px ui-monospace,Menlo,monospace;color:#0f172a;margin:4px 0;word-break:break-all">' + esc(ib) + '</div><button type="button" data-iban="' + esc(a.iban) + '" style="border:1px solid #cbd5e1;background:#fff;border-radius:8px;padding:6px 12px;font-weight:600;font-size:12px;cursor:pointer">IBAN\'ı kopyala</button></div>';
    });
    if (PAY.note) h += '<div style="font-size:12px;color:#64748b;margin-top:4px">' + esc(PAY.note) + '</div>';
    h += '<div style="margin-top:10px"><button id="spx-pn" style="width:100%;border:0;background:#0a1f44;color:#fff;border-radius:10px;padding:12px;font-weight:700;font-size:14px">💸 Ödeme yaptım (şirkete bildir)</button><div id="spx-pnf" style="display:none;margin-top:8px"><input id="spx-pna" type="number" inputmode="decimal" placeholder="Ödenen tutar (TL)" style="width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:8px;margin-bottom:6px"><input id="spx-pnn" placeholder="Not (dekont no, banka vb.)" style="width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:8px;margin-bottom:6px"><button id="spx-pns" style="width:100%;border:0;background:#f27a1a;color:#fff;border-radius:10px;padding:12px;font-weight:700">Gönder</button><div id="spx-pnm" style="margin-top:6px;font-size:13px;font-weight:600"></div></div></div>';
    h += '</div>';
    mn.insertAdjacentHTML('afterbegin', h);
    document.getElementById('spx-pn').onclick = function () { var f = document.getElementById('spx-pnf'); f.style.display = f.style.display === 'none' ? 'block' : 'none'; };
    document.getElementById('spx-pns').onclick = function () {
      var m = document.getElementById('spx-pnm'), amt = parseFloat(document.getElementById('spx-pna').value);
      if (!(amt > 0)) { m.style.color = '#b91c1c'; m.textContent = 'Geçerli bir tutar girin'; return; }
      pcall('POST', '/tech/payment-notice', { amount: amt, note: document.getElementById('spx-pnn').value }).then(function () { m.style.color = '#16a34a'; m.textContent = '✔ Bildiriminiz yöneticiye iletildi. Onaylanınca bakiyenize yansır.'; document.getElementById('spx-pna').value = ''; }).catch(function (e) { m.style.color = '#b91c1c'; m.textContent = e.message; });
    };
    document.getElementById('spx-pay').onclick = function (e) { var b = e.target.closest('button[data-iban]'); if (!b) return; var v = b.getAttribute('data-iban'); (navigator.clipboard ? navigator.clipboard.writeText(v) : Promise.reject()).then(function () { toast('IBAN kopyalandı'); }).catch(function () { toast(v); }); };
  }
  setInterval(payCard, 600);

  /* ---------- admin: Yorumlar sayfasında "Sitede müşteri yorumları" açma/kapama ---------- */
  var SRS = null, SRBUSY = false;
  function reviewsToggle() {
    var ex = document.getElementById('spx-sr'), onPg = /^\/admin\/reviews\/?$/.test(location.pathname), mn = document.querySelector('main');
    if (!onPg || !mn) { if (ex) ex.remove(); return; }
    if (!SRS) { if (!SRBUSY) { SRBUSY = true; pcall('GET', '/site-reviews-settings').then(function (r) { SRS = r; }).catch(function () { }).then(function () { SRBUSY = false; }); } return; }
    if (ex) return;
    var d = document.createElement('div'); d.id = 'spx-sr'; d.style.cssText = 'background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:14px 16px;margin-bottom:16px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between';
    d.innerHTML = '<div style="flex:1;min-width:240px"><b style="color:#0a1f44">Sitede “' + esc(SRS.title) + '” bölümü</b><div style="font-size:12.5px;color:#64748b;margin-top:3px">Açıkken sitedeki sayfaların alt bilgisinin üstünde <b>yalnızca “Yayında” durumundaki gerçek yorumlar</b> gösterilir. Marka sayfasında yalnız o markanın, kategori sayfasında o kategorinin yorumları çıkar. Yorum yoksa bölüm görünmez.</div></div><label class="spx-sw-l" style="display:flex;align-items:center;gap:8px;font-weight:600">' + sw('spx-sr-on', SRS.enabled) + ' <span id="spx-sr-t">' + (SRS.enabled ? 'Açık' : 'Kapalı') + '</span></label>';
    mn.insertAdjacentElement('afterbegin', d);
    document.getElementById('spx-sr-on').onchange = function () { var v = this.checked; pcall('PUT', '/site-reviews-settings', { enabled: v }).then(function (r) { SRS = r; document.getElementById('spx-sr-t').textContent = v ? 'Açık' : 'Kapalı'; toast(v ? 'Yorum bölümü sitede açıldı' : 'Yorum bölümü kapatıldı'); }).catch(function (e) { fail(e); document.getElementById('spx-sr-on').checked = !v; }); };
  }
  setInterval(reviewsToggle, 900);

  /* ---------- usta: alt menü rozetleri (Görevler / Teklif / Duyuru = adet, Bakiyem = borç varsa !) ---------- */
  var BDG = null, BDGT = 0, BDGBUSY = false, BDGP = '';
  function techBadges() {
    if (!document.body.classList.contains('spx-tech')) return;
    var now = Date.now(); if (BDGP !== location.pathname) { BDGP = location.pathname; BDGT = 0; }
    if (!BDGBUSY && (!BDG || now - BDGT > 30000)) {
      BDGBUSY = true;
      pcall('GET', '/tech/badges').then(function (r) { var o = BDG; BDG = r; if (o && r.jobs > o.jobs) { ding(); bnotify('Yeni iş atandı', (r.jobs - o.jobs) + ' yeni iş atandı'); } }).catch(function () { }).then(function () { BDGT = Date.now(); BDGBUSY = false; });
    }
    if (!BDG) return;
    var tb = document.getElementById('spx-tb'), seen = ''; try { seen = sessionStorage.getItem('spx_tb'); } catch (e) { }
    if (BDG.jobs > 0 && !seen && !tb && /^\/tech\/?$/.test(location.pathname)) {
      tb = document.createElement('div'); tb.id = 'spx-tb'; tb.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:9999;background:#f27a1a;color:#fff;padding:11px 14px;font-weight:700;font-size:14px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 10px rgba(0,0,0,.2)';
      tb.innerHTML = '<span>📋 ' + BDG.jobs + ' yeni işiniz var</span><button aria-label="Kapat" style="border:0;background:none;color:#fff;font-size:20px;cursor:pointer">×</button>';
      tb.onclick = function () { try { sessionStorage.setItem('spx_tb', '1'); } catch (e) { } tb.remove(); }; document.body.appendChild(tb); setTimeout(function () { var x = document.getElementById('spx-tb'); if (x) x.remove(); try { sessionStorage.setItem('spx_tb', '1'); } catch (e) { } }, 9000);
    }
    var map = { 'tab-jobs': BDG.jobs, 'tab-quotes': BDG.quotes, 'tab-announcements': BDG.ann, 'tab-balance': BDG.debt > 0 ? '!' : 0 };
    Object.keys(map).forEach(function (k) {
      var a = document.querySelector('nav a[data-testid="' + k + '"]'); if (!a) return;
      var host = a.querySelector('span.relative') || a, b = host.querySelector('.spx-bdg'), v = map[k];
      if (!v) { if (b) b.remove(); return; }
      if (!b) { b = document.createElement('span'); b.className = 'spx-bdg'; b.style.cssText = 'position:absolute;top:-6px;right:-10px;background:#ef4444;color:#fff;font-size:10px;font-weight:700;border-radius:99px;min-width:16px;height:16px;padding:0 4px;display:flex;align-items:center;justify-content:center;line-height:1'; host.appendChild(b); }
      var t = v > 99 ? '99+' : String(v); if (b.textContent !== t) b.textContent = t;
      if (k === 'tab-balance') b.title = 'Şirkete borcunuz var: ' + BDG.debt + ' ₺';
    });
  }
  setInterval(techBadges, 1000);
  document.addEventListener('visibilitychange', function () { BDGT = 0; });
  window.addEventListener('popstate', function () { BDGT = 0; });

  /* ---------- usta: "Puanım" kartı (ana ekran) ---------- */
  var SCR = null, SCRT = 0, SCRBUSY = false;
  function scoreCard() {
    if (!document.body.classList.contains('spx-tech')) return;
    var on = /^\/tech\/?$/.test(location.pathname), ex = document.getElementById('spx-score');
    if (!on) { if (ex) ex.remove(); return; }
    var mn = document.querySelector('main'); if (!mn) return;
    if (!SCR || Date.now() - SCRT > 300000) {
      if (!SCRBUSY) { SCRBUSY = true; pcall('GET', '/tech-rating/my').then(function (r) { SCR = r; SCRT = Date.now(); }).catch(function () { SCR = SCR || { me: null }; SCRT = Date.now() - 240000; }).then(function () { SCRBUSY = false; if (ex) ex.remove(); }); }
      if (!SCR) return;
    }
    if (ex || !SCR.me) return;
    var m = SCR.me, LV = { Platin: '#7c3aed', 'Altın': '#d97706', 'Gümüş': '#64748b', Bronz: '#b45309', 'Gelişim': '#dc2626', Yeni: '#0891b2' };
    var h = '<div id="spx-score" class="notranslate" style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:14px;margin-bottom:12px"><div style="display:flex;align-items:center;gap:10px;justify-content:space-between"><div><div style="font-size:12px;color:#64748b;font-weight:600;letter-spacing:.04em;text-transform:uppercase">Puanım (son 90 gün)</div><div style="font-size:28px;font-weight:800;color:#0a1f44;line-height:1.1">' + m.score + '<span style="font-size:14px;color:#64748b;font-weight:600"> /100</span></div></div><div style="text-align:right"><span style="display:inline-block;background:' + (LV[m.level] || '#64748b') + ';color:#fff;border-radius:20px;padding:4px 12px;font-weight:700;font-size:13px">' + esc(m.level) + '</span>' + (SCR.rank ? '<div style="font-size:12px;color:#64748b;margin-top:4px">Sıralama ' + SCR.rank + ' / ' + SCR.of + '</div>' : '') + '</div></div>' +
      '<div style="background:#e2e8f0;border-radius:6px;height:8px;margin:10px 0 8px"><div style="width:' + Math.min(100, m.score) + '%;height:8px;border-radius:6px;background:' + (LV[m.level] || '#1155cc') + '"></div></div>';
    if (m.done < 5) h += '<div style="font-size:13px;color:#475569">Seviyeniz ilk 5 tamamlanan işten sonra belirlenir (' + m.done + '/5).</div>';
    if (m.weak && m.weak.length) h += '<div style="font-size:13px;color:#475569"><b>Puanı yükseltmek için:</b> ' + esc(m.weak[0].tip) + '</div>';
    (SCR.notes || []).slice(0, 2).forEach(function (n) { h += '<div style="font-size:13px;color:#166534;background:#f0fdf4;border-radius:8px;padding:6px 10px;margin-top:6px">' + (n.kind === 'övgü' ? '👏 ' : '') + esc(n.text) + '</div>'; });
    h += '</div>';
    mn.insertAdjacentHTML('afterbegin', h);
  }
  setInterval(scoreCard, 800);

  /* ---------- Site Yönetimi (gerçek panel API'si) ---------- */
  var API = (window.SP_PANEL_API || location.origin + '/api');
  var ov, TAB = 'moduller', MOD = null, FEAT = null;
  function toast(t) { var d = $('#spx-toast') || (function () { var x = document.createElement('div'); x.id = 'spx-toast'; document.body.appendChild(x); return x; })(); d.textContent = t; d.style.display = 'block'; clearTimeout(d._t); d._t = setTimeout(function () { d.style.display = 'none'; }, 3200); }
  function call(method, path, body) {
    var o = { method: method, headers: { Authorization: 'Bearer ' + LS.get('token', '') } };
    if (body !== undefined) { o.headers['Content-Type'] = 'application/json'; o.body = JSON.stringify(body); }
    return fetch(API + path, o).then(function (r) { return r.text().then(function (t) { var j = {}; try { j = JSON.parse(t); } catch (e) { } if (!r.ok) { var d = j && j.detail; throw new Error(typeof d === 'string' ? d : (d && d[0] && d[0].msg) || ('Hata ' + r.status)); } return j; }); });
  }
  function fail(e) { toast(e.message || 'İşlem başarısız'); }
  var TABS = [['firmalar', 'Firmalar'], ['moduller', 'Aç / Kapat & Ayarlar'], ['seo', 'SEO · 301 · 404'], ['yeni', 'Yeni Sipariş'], ['pazar', 'Pazaryerleri'], ['yetki', 'Kullanıcılar & Yetkiler'], ['gsc', 'Google Search Console'], ['urunler', 'Ürün Yönetimi'], ['marka', 'Marka Ürün Aktarma'], ['m360', 'Müşteri 360'], ['kaynak', 'Kaynak & Arama Analizi'], ['ustapuan', 'Usta Puanlama'], ['ustagecmis', 'Usta İş Geçmişi'], ['cari', 'Cari & Trend'], ['tahsilat', 'Teknisyen Tahsilat'], ['atolye', 'Atölye'], ['canli', 'Canlı Ziyaretçiler'], ['wa', 'WhatsApp & Bildirim'], ['daha', 'Daha Fazlası'], ['bildirim', 'Bildirimler'], ['memnun', 'Müşteri Memnuniyeti'], ['vade', 'Usta Borç Vadesi'], ['harita', 'Günün İş Haritası'], ['onay', 'Onay Bekleyenler'], ['rapor', 'Rapor Merkezi'], ['kurulum', 'Kurulum Durumu']];
  function build() {
    ov = document.createElement('div'); ov.id = 'spx-ov';
    ov.innerHTML = '<header><button class="spx-b" id="spx-menu">☰ Menü</button><h2 id="spx-h">Site Yönetimi</h2><button class="spx-b" id="spx-x">Kapat ✕</button></header><div id="spx-tabs"></div><div id="spx-body">Yükleniyor…</div>';
    document.body.appendChild(ov); $('#spx-x').onclick = function () { ov.classList.remove('on'); markActive(); }; $('#spx-menu').onclick = function () { var o = document.querySelector('[data-testid=open-sidebar]'); if (o) o.click(); };
    $('#spx-tabs').innerHTML = TABS.map(function (t) { return '<button data-t="' + t[0] + '">' + t[1] + '</button>'; }).join('');
    $('#spx-tabs').onclick = function (e) { var b = e.target.closest('button'); if (b) { TAB = b.getAttribute('data-t'); draw(); markActive(); } };
  }
  function open(tab) { if (!ov) build(); if (tab) TAB = tab; ov.classList.add('on'); draw(); markActive(); }
  function sw(id, on) { return '<label class="spx-sw"><input type="checkbox" id="' + id + '"' + (on ? ' checked' : '') + '><i></i></label>'; }
  function body() { return $('#spx-body'); }
  function draw() {
    Array.prototype.forEach.call($('#spx-tabs').children, function (b) { b.classList.toggle('on', b.getAttribute('data-t') === TAB); });
    var hh = $('#spx-h'); if (hh) hh.textContent = ({ firmalar: 'Firmalar', daha: 'Daha Fazlası', bildirim: 'Bildirimler', memnun: 'Müşteri Memnuniyeti', vade: 'Usta Borç Vadesi', harita: 'Günün İş Haritası', moduller: 'Aç/Kapat & Entegrasyonlar', seo: 'SEO · 301 · 404', yeni: 'Yeni Sipariş Gir', pazar: 'Pazaryerleri', yetki: 'Kullanıcılar & Yetkiler', gsc: 'Google Search Console', marka: 'Marka Ürün Aktarma', urunler: 'Ürün Yönetimi', m360: 'Müşteri 360', kaynak: 'Kaynak & Arama Analizi', ustapuan: 'Usta Puanlama', ustagecmis: 'Usta İş Geçmişi', cari: 'Cari & Trend', tahsilat: 'Teknisyen Tahsilat', atolye: 'Atölye (Cihaz Teslim Alma)', sohbet: 'Canlı Sohbet', canli: 'Canlı Ziyaretçiler', wa: 'WhatsApp & Bildirim Ayarları', onay: 'Onay Bekleyenler', rapor: 'Rapor Merkezi', kurulum: 'Kurulum Durumu' })[TAB];
    body().innerHTML = 'Yükleniyor…';
    ({ firmalar: drawFirmalar, daha: drawDaha, bildirim: drawBildirim, memnun: drawMemnun, vade: drawVade, harita: drawHarita, moduller: drawMod, seo: drawSeo, yeni: drawNew, pazar: drawMkt, yetki: drawUsers, gsc: drawGsc, marka: drawBrand, urunler: drawProducts, m360: drawM360, kaynak: drawKaynak, ustapuan: drawUstaPuan, ustagecmis: drawUstaGecmis, cari: drawCari, tahsilat: drawTahsilat, atolye: drawAtolye, sohbet: drawSohbet, canli: drawCanli, wa: drawWa, onay: drawOnay, rapor: drawRapor, kurulum: drawKurulum })[TAB]();
  }
  /* ===== Firmalar: paneli kendi verisiyle kullanan müşteri firmalar ===== */
  var FM = { sel: '', tab: 'bilgi', job: '', q: '', flt: '', newOpen: false };
  var FST = { yeni: 'Yeni', atandi: 'Atandı', yolda: 'Yolda', basladi: 'Başladı', tamamlandi: 'Tamamlandı', faturalandi: 'Faturalandı', iptal: 'İptal' };
  function fmD(s) { if (!s) return '—'; var d = new Date(s); return isNaN(d) ? esc(String(s)) : d.toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
  function fmFeat(F, labels, pre) { return Object.keys(labels).map(function (k) { return '<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #eef2f6"><span>' + esc(labels[k]) + '</span>' + sw(pre + k, F[k] !== false) + '</div>'; }).join(''); }
  function fmFeatVals(labels, pre) { var o = {}; Object.keys(labels).forEach(function (k) { var e = document.getElementById(pre + k); o[k] = !!(e && e.checked); }); return o; }
  function fmLogo(id, cb) {
    var el = document.getElementById(id), f = el && el.files && el.files[0];
    if (!f) { cb(null); return; }
    if (f.size > 800 * 1024) { toast('Logo 800 KB\'dan küçük olmalı'); return; }
    var r = new FileReader(); r.onload = function () { cb(r.result); }; r.readAsDataURL(f);
  }
  function fmMoney(n) { return '₺' + (Math.round((n || 0) * 100) / 100).toLocaleString('tr-TR', { minimumFractionDigits: 0, maximumFractionDigits: 2 }); }
  function fmState(f) { return f.status === 'askida' ? ['Askıda', '#fee2e2', '#b91c1c'] : (f.expired ? ['Süresi doldu', '#fef3c7', '#b45309'] : ['Aktif', '#dcfce7', '#15803d']); }
  function fmPill(f) { var s = fmState(f); return '<span class="spx-pill" style="background:' + s[1] + ';color:' + s[2] + '">' + s[0] + '</span>'; }
  function fmLeft(f) { if (!f.expires_at) return 'Sınırsız'; if (f.expired) return 'süre doldu'; return 'kalan ' + Math.max(0, Math.ceil((new Date(f.expires_at) - new Date()) / 864e5)) + ' gün'; }
  function fmKv(k, v) { return '<div style="padding:7px 0;border-bottom:1px solid #eef2f6"><small style="color:#64748b;display:block">' + k + '</small><b style="font-weight:600">' + (v || '—') + '</b></div>'; }
  function fmMini(t, v, c) { return '<div style="flex:1 1 90px;background:' + (c || '#f8fafc') + ';border-radius:10px;padding:8px 10px;min-width:0"><small style="color:#64748b;display:block;white-space:nowrap">' + t + '</small><b style="font-size:15px">' + v + '</b></div>'; }
  function drawFirmalar() {
    Promise.all([call('GET', '/admin/firms'), call('GET', '/admin/firm-template')]).then(function (a) {
      var list = a[0].firms || [], L = a[0].feature_labels || {}, tpl = a[1], f0 = list.filter(function (x) { return x.id === FM.sel; })[0];
      if (FM.sel && !f0) FM.sel = '';
      var h = '';
      if (!f0) h = fmListHtml(list, L, tpl); else h = fmDetailHtml(f0, L);
      body().innerHTML = h;
      if (!f0) fmListBind(list, L); else fmDetailBind(f0, L);
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  function fmListHtml(list, L, tpl) {
    var act = 0, ask = 0, exp = 0, rev = 0, mon = 0, open = 0, done = 0, cus = 0;
    list.forEach(function (f) { if (f.status === 'askida') ask++; else if (f.expired) exp++; else act++; rev += f.stats.revenue_total || 0; mon += f.stats.revenue_month || 0; open += f.stats.open; done += f.stats.done; cus += f.stats.customers; });
    var q = (FM.q || '').toLowerCase(), shown = list.filter(function (f) {
      if (FM.flt === 'aktif' && (f.status === 'askida' || f.expired)) return false; if (FM.flt === 'askida' && f.status !== 'askida') return false; if (FM.flt === 'doldu' && !f.expired) return false;
      return !q || (f.name + ' ' + f.login_email + ' ' + (f.contact_name || '') + ' ' + (f.phone || '')).toLowerCase().indexOf(q) >= 0;
    });
    var h = '<div style="display:flex;gap:8px;flex-wrap:wrap">' + fmMini('Firma', list.length + ' <small style="font-weight:400;color:#64748b">(' + act + ' aktif' + (ask ? ', ' + ask + ' askıda' : '') + (exp ? ', ' + exp + ' süresi dolan' : '') + ')</small>', '#eff6ff') + fmMini('Toplam ciro', fmMoney(rev), '#f0fdf4') + fmMini('Bu ay ciro', fmMoney(mon), '#ecfeff') + fmMini('Açık iş', open, '#fffbeb') + fmMini('Tamamlanan', done, '#f8fafc') + fmMini('Müşteri', cus, '#f8fafc') + '</div>';
    h += '<div class="spx-card" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><input id="fm_q" placeholder="Firma, kullanıcı adı, telefon ara…" value="' + esc(FM.q || '') + '" style="flex:1 1 200px;padding:9px;border:1px solid #cbd5e1;border-radius:9px"><select id="fm_f" style="padding:9px;border:1px solid #cbd5e1;border-radius:9px">' + [['', 'Tümü'], ['aktif', 'Aktif'], ['askida', 'Askıda'], ['doldu', 'Süresi dolan']].map(function (o) { return '<option value="' + o[0] + '"' + (FM.flt === o[0] ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select><button class="spx-b p" id="fm_new">＋ Yeni firma</button></div>';
    if (FM.newOpen) h += '<div class="spx-card"><b>Yeni firma</b><small style="display:block;color:#64748b;margin-bottom:8px">Gireceğiniz kullanıcı adı ve şifreyle giren firma, Usta ekranlarını KENDİ verisiyle kullanır; sizin işlerinizi ve müşterilerinizi görmez. Firma bilgileri servis fişine ve KVKK metnine otomatik yazılır.</small><div class="spx-g"><label>Firma adı *<input id="fm_n"></label><label>Yetkili ad soyad<input id="fm_c"></label><label>Telefon<input id="fm_t"></label><label>Adres<input id="fm_a"></label><label>Vergi no<input id="fm_v"></label><label>Vergi dairesi<input id="fm_vd"></label><label>Kullanıcı adı (e-posta) *<input id="fm_e" type="email"></label><label>Şifre (en az 8) *<input id="fm_p" type="text"></label><label>Kullanım günü (boş = sınırsız)<input id="fm_u" type="number" min="1" placeholder="örn. 30"></label><label>Logo<input id="fm_l" type="file" accept="image/png,image/jpeg,image/webp"></label></div><div style="margin:10px 0"><b>Ek özellikler</b>' + fmFeat({}, L, 'fmf_') + '</div><button class="spx-b p" id="fm_go">Firmayı kaydet</button> <button class="spx-b" id="fm_nx">Vazgeç</button></div>';
    h += shown.length ? '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:10px">' + shown.map(function (f) {
      var s = f.stats;
      return '<div class="spx-card" style="margin:0"><div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start"><div style="min-width:0"><b style="font-size:16px">' + esc(f.name) + '</b>' + ((f.self_edits || []).length ? ' <span title="Firma bilgilerini kendisi güncelledi" style="color:#d97706">✎</span>' : '') + '<br><small style="color:#64748b;word-break:break-all">' + esc(f.login_email) + ((f.users || []).length ? ' · +' + f.users.length + ' kullanıcı' : '') + '</small></div>' + fmPill(f) + '</div>' +
        '<div style="font-size:13px;color:#475569;margin:6px 0">' + (f.contact_name ? esc(f.contact_name) + ' · ' : '') + esc(f.phone || '') + (f.address ? '<br>' + esc(f.address) : '') + '</div>' +
        '<div style="display:flex;gap:6px;flex-wrap:wrap">' + fmMini('Toplam ciro', fmMoney(s.revenue_total), '#f0fdf4') + fmMini('Bu ay', fmMoney(s.revenue_month), '#ecfeff') + fmMini('Açık', s.open, '#fffbeb') + fmMini('Biten', s.done) + fmMini('Müşteri', s.customers) + fmMini('Ort. iş', fmMoney(s.avg_ticket)) + '</div>' +
        '<div style="font-size:12px;color:#64748b;margin:8px 0">Eklendi: ' + fmD(f.created_at) + ' · Bitiş: ' + (f.expires_at ? fmD(f.expires_at) + ' (' + fmLeft(f) + ')' : 'Sınırsız') + '<br>Son işlem: ' + fmD(s.last_activity) + '</div>' +
        '<button class="spx-b p" data-fsel="' + f.id + '" style="width:100%">Detay / Düzenle</button></div>';
    }).join('') + '</div>' : '<div class="spx-card" style="color:#64748b">' + (list.length ? 'Aramaya uyan firma yok.' : 'Henüz firma yok. “＋ Yeni firma” ile ilk firmayı ekleyin.') + '</div>';
    h += '<div class="spx-card"><b>Servis fişi / KVKK alt metni (tüm firmalar için ortak)</b><small style="display:block;color:#64748b;margin:4px 0 8px">Her firmanın fişine bu metin yazılır (firma kendi metnini yazmadıysa). {firma_adi}, {adres}, {telefon} yerine firmanın bilgileri otomatik gelir. Kaydedince tüm firmalar güncellenir. Nihai metni hukuken kontrol ettirin.</small><textarea id="ft_n" rows="5" style="width:100%">' + esc(tpl.pdf_note) + '</textarea><div style="margin-top:8px"><button class="spx-b p" id="ft_go">Metni kaydet</button> <button class="spx-b" id="ft_main">ServisPlus metninden oluştur</button></div></div>';
    return h;
  }
  function fmListBind(list, L) {
    var go = function (id) { FM.sel = id; FM.tab = 'bilgi'; FM.job = ''; drawFirmalar(); window.scrollTo(0, 0); };
    body().onclick = function (e) { var s = e.target.closest('[data-fsel]'); if (s) go(s.getAttribute('data-fsel')); };
    $('#fm_q').oninput = function () { FM.q = this.value; var p = this.selectionStart; drawFirmalar(); setTimeout(function () { var i = $('#fm_q'); if (i) { i.focus(); i.setSelectionRange(p, p); } }, 60); };
    $('#fm_f').onchange = function () { FM.flt = this.value; drawFirmalar(); };
    $('#fm_new').onclick = function () { FM.newOpen = !FM.newOpen; drawFirmalar(); };
    if ($('#fm_nx')) $('#fm_nx').onclick = function () { FM.newOpen = false; drawFirmalar(); };
    if ($('#fm_go')) $('#fm_go').onclick = function () {
      var n = $('#fm_n').value.trim(), e = $('#fm_e').value.trim(), p = $('#fm_p').value;
      if (!n || !e || p.length < 8) { toast('Firma adı, kullanıcı adı ve en az 8 karakterli şifre gerekli'); return; }
      fmLogo('fm_l', function (lg) {
        var b = { name: n, contact_name: $('#fm_c').value, phone: $('#fm_t').value, address: $('#fm_a').value, tax_no: $('#fm_v').value, tax_office: $('#fm_vd').value, email: e, password: p, features: fmFeatVals(L, 'fmf_') };
        if (lg) b.logo = lg; if ($('#fm_u').value) b.usage_days = parseInt($('#fm_u').value, 10);
        call('POST', '/admin/firms', b).then(function () { toast('Firma eklendi'); FM.newOpen = false; drawFirmalar(); }).catch(fail);
      });
    };
    $('#ft_go').onclick = function () { call('PUT', '/admin/firm-template', { pdf_note: $('#ft_n').value }).then(function (r) { toast('Kaydedildi (' + r.updated_firms + ' firma güncellendi)'); }).catch(fail); };
    $('#ft_main').onclick = function () { if (!confirm('ServisPlus\'ın kendi PDF notu alınıp ServisPlus adı/telefonu yerine firma bilgileri konacak ve tüm firmalara uygulanacak. Devam?')) return; call('POST', '/admin/firm-template/from-main', {}).then(function (r) { $('#ft_n').value = r.pdf_note; toast('Oluşturuldu (' + r.updated_firms + ' firma güncellendi)'); }).catch(fail); };
  }
  function fmDetailHtml(f, L) {
    var s = f.stats, tabs = [['bilgi', 'Bilgiler'], ['isler', 'İşler (' + s.total + ')'], ['ciro', 'Ciro raporu'], ['kul', 'Kullanıcılar (' + (1 + (f.users || []).length) + ')']];
    var h = '<div class="spx-card"><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><button class="spx-b" id="fd_back">‹ Firmalar</button><b style="font-size:18px;flex:1;min-width:150px">' + esc(f.name) + '</b>' + fmPill(f) + '<button class="spx-b ' + (f.status === 'askida' ? 'p' : 'd') + '" id="fe_st">' + (f.status === 'askida' ? 'Yeniden aktifleştir' : 'Askıya al') + '</button></div>' +
      '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px">' + fmMini('Toplam ciro', fmMoney(s.revenue_total), '#f0fdf4') + fmMini('Bu ay ciro', fmMoney(s.revenue_month), '#ecfeff') + fmMini('Bu ay iş', s.jobs_month) + fmMini('Açık iş', s.open, '#fffbeb') + fmMini('Biten', s.done) + fmMini('İptal', s.cancelled || 0) + fmMini('Müşteri', s.customers) + fmMini('Ort. iş', fmMoney(s.avg_ticket)) + '</div></div>';
    h += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin:8px 0">' + tabs.map(function (t) { return '<button class="spx-b' + (FM.tab === t[0] ? ' p' : '') + '" data-ftab="' + t[0] + '">' + t[1] + '</button>'; }).join('') + '</div><div id="fd_tab"></div>';
    return h;
  }
  function fmDetailBind(f, L) {
    $('#fd_back').onclick = function () { FM.sel = ''; FM.job = ''; drawFirmalar(); };
    $('#fe_st').onclick = function () { var st = f.status === 'askida' ? 'aktif' : 'askida'; if (st === 'askida' && !confirm('Firma girişi kapatılsın mı?')) return; call('PUT', '/admin/firms/' + f.id, { status: st }).then(function () { toast(st === 'askida' ? 'Askıya alındı' : 'Aktifleştirildi'); drawFirmalar(); }).catch(fail); };
    body().onclick = function (e) {
      var t = e.target.closest('[data-ftab]'); if (t) { FM.tab = t.getAttribute('data-ftab'); FM.job = ''; drawFirmalar(); return; }
      var ut = e.target.closest('[data-fut]'); if (ut) { call('PUT', '/admin/firms/' + f.id + '/users/' + ut.getAttribute('data-fut'), { active: ut.getAttribute('data-on') === '1' }).then(function () { toast('Güncellendi'); drawFirmalar(); }).catch(fail); return; }
      var ud = e.target.closest('[data-fud]'); if (ud) { if (!confirm('Kullanıcı silinsin mi?')) return; call('DELETE', '/admin/firms/' + f.id + '/users/' + ud.getAttribute('data-fud')).then(function () { toast('Silindi'); drawFirmalar(); }).catch(fail); return; }
      var jd = e.target.closest('[data-fjd]'); if (jd) { e.stopPropagation(); if (!confirm('Bu iş kalıcı olarak silinsin mi? Geri alınamaz.')) return; call('DELETE', '/admin/firms/' + f.id + '/jobs/' + jd.getAttribute('data-fjd')).then(function () { toast('İş silindi'); FM.job = ''; drawFirmalar(); }).catch(fail); return; }
      var o = e.target.closest('[data-fo]'); if (o) { FM.job = o.getAttribute('data-fo'); fmJobs(f.id); }
    };
    var tab = $('#fd_tab');
    if (FM.tab === 'isler') { tab.innerHTML = '<div id="fm_jobs"></div>'; fmJobs(f.id); }
    else if (FM.tab === 'ciro') { tab.innerHTML = '<div class="spx-card">Yükleniyor…</div>'; call('GET', '/admin/firms/' + f.id + '/report?months=12').then(function (r) { tab.innerHTML = '<div class="spx-card">' + fmReportHtml(r) + '</div>'; }).catch(function (e) { tab.innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; }); }
    else if (FM.tab === 'kul') {
      tab.innerHTML = '<div class="spx-card"><b>Kullanıcılar</b> <small style="color:#64748b">(ana hesap + en fazla 3)</small><div style="padding:8px 0;border-bottom:1px solid #eef2f6"><b>Ana hesap</b> <small style="color:#64748b">' + esc(f.login_email) + ' · eklendi ' + fmD(f.created_at) + '</small></div>' +
        ((f.users || []).map(function (u) { return '<div style="display:flex;justify-content:space-between;align-items:center;gap:6px;padding:8px 0;border-bottom:1px solid #eef2f6"><span>' + esc(u.name || '') + ' <small style="color:#64748b">' + esc(u.email) + ' · eklendi ' + fmD(u.created_at) + '</small>' + (u.active === false ? ' <small style="color:#b91c1c">(kapalı)</small>' : '') + '</span><span><button class="spx-b" data-fut="' + u.id + '" data-on="' + (u.active === false ? '1' : '0') + '">' + (u.active === false ? 'Aç' : 'Kapat') + '</button> <button class="spx-b d" data-fud="' + u.id + '">Sil</button></span></div>'; }).join('') || '<div style="color:#64748b;padding:8px 0">Ek kullanıcı yok.</div>') + '</div>';
    } else {
      var se = (f.self_edits || []).slice(-8).reverse();
      tab.innerHTML = '<div class="spx-card"><b>Firma bilgileri</b><div class="spx-g" style="margin-top:6px">' + fmKv('Firma adı', esc(f.name)) + fmKv('Yetkili', esc(f.contact_name || '')) + fmKv('Telefon', esc(f.phone || '')) + fmKv('Adres', esc(f.address || '')) + fmKv('Vergi no', esc(f.tax_no || '')) + fmKv('Vergi dairesi', esc(f.tax_office || '')) + fmKv('Kullanıcı adı', esc(f.login_email)) + fmKv('Eklenme tarihi', fmD(f.created_at)) + fmKv('Kullanım bitişi', f.expires_at ? fmD(f.expires_at) + ' (' + fmLeft(f) + ')' : 'Sınırsız') + fmKv('Son işlem', fmD(f.stats.last_activity)) + fmKv('Logo', f.has_logo ? 'Yüklü' : 'Yok') + fmKv('Ek kullanıcı', (f.users || []).length + ' / 3') + '</div></div>' +
        (se.length ? '<div class="spx-card" style="background:#fffbeb;border-color:#fde68a"><b>Firmanın kendi yaptığı değişiklikler</b><div style="font-size:13px;margin-top:4px">' + se.map(function (x) { return fmD(x.at) + ' — ' + esc((x.fields || []).join(', ')); }).join('<br>') + '</div></div>' : '') +
        '<div class="spx-card"><b>Düzenle</b><div class="spx-g" style="margin-top:8px"><label>Firma adı<input id="fe_n" value="' + esc(f.name) + '"></label><label>Yetkili<input id="fe_c" value="' + esc(f.contact_name || '') + '"></label><label>Telefon<input id="fe_t" value="' + esc(f.phone || '') + '"></label><label>Adres<input id="fe_a" value="' + esc(f.address || '') + '"></label><label>Vergi no<input id="fe_v" value="' + esc(f.tax_no || '') + '"></label><label>Vergi dairesi<input id="fe_vd" value="' + esc(f.tax_office || '') + '"></label><label>Kullanıcı adı (e-posta)<input id="fe_e" value="' + esc(f.login_email) + '"></label><label>Yeni şifre (boşsa değişmez)<input id="fe_p" placeholder="en az 8 karakter"></label>' +
        '<label>Kullanım günü (bugünden başlar, 0 = sınırsız)<input id="fe_u" type="number" min="0" placeholder="' + (f.expires_at ? 'bitiş: ' + fmD(f.expires_at) : 'sınırsız') + '"></label><label>Logo ' + (f.has_logo ? '(yüklü — değiştirmek için seçin)' : '(yok)') + '<input id="fe_l" type="file" accept="image/png,image/jpeg,image/webp"></label></div>' + (f.has_logo ? '<label style="display:block;margin:6px 0"><input type="checkbox" id="fe_lx"> Logoyu kaldır</label>' : '') +
        '<div style="margin:10px 0"><b>Ek özellikler</b>' + fmFeat(f.features || {}, L, 'fef_') + '</div><button class="spx-b p" id="fe_go">Kaydet</button></div>';
      $('#fe_go').onclick = function () {
        var b = { name: $('#fe_n').value, contact_name: $('#fe_c').value, phone: $('#fe_t').value, address: $('#fe_a').value, tax_no: $('#fe_v').value, tax_office: $('#fe_vd').value, email: $('#fe_e').value, features: fmFeatVals(L, 'fef_') };
        if ($('#fe_p').value) b.password = $('#fe_p').value; if ($('#fe_lx') && $('#fe_lx').checked) b.logo = ''; if ($('#fe_u').value !== '') b.usage_days = parseInt($('#fe_u').value, 10);
        fmLogo('fe_l', function (lg) { if (lg) b.logo = lg; call('PUT', '/admin/firms/' + f.id, b).then(function () { toast('Kaydedildi'); drawFirmalar(); }).catch(fail); });
      };
    }
  }
  function fmJobs(fid) {
    var box = $('#fm_jobs'); if (!box) return;
    box.innerHTML = '<div class="spx-card">Yükleniyor…</div>';
    var p = [call('GET', '/admin/firms/' + fid + '/jobs?limit=200')]; if (FM.job) p.push(call('GET', '/admin/firms/' + fid + '/jobs/' + FM.job));
    Promise.all(p).then(function (a) {
      var r = a[0], h = '<div class="spx-card"><b>' + esc(r.firm.name) + ' — işler</b> <button class="spx-b" id="fm_jx" style="float:right">Yenile</button>' + (r.jobs.length ? tbl(['No', 'Müşteri', 'Cihaz', 'Arıza', 'Adım', 'Tutar', 'Açılış', ''], r.jobs.map(function (j) {
        return tr_([esc(j.job_number || ''), esc(j.customer_name || '') + '<br><small style="color:#64748b">' + esc(j.customer_phone || '') + '</small>', esc((j.device_brand_name ? j.device_brand_name + ' ' : '') + (j.device_type || '')), esc((j.fault_description || '').slice(0, 60)), '<span class="spx-pill">' + esc(FST[j.status] || j.status) + '</span>', j.total_amount ? money(j.total_amount) : '—', fmD(j.created_at), '<button class="spx-b d" data-fjd="' + j.id + '">Sil</button>'], 'data-fo="' + j.id + '"');
      })) : '<p style="color:#64748b">Bu firmanın henüz işi yok.</p>') + '</div>';
      if (a[1]) {
        var j = a[1], st = ['yeni', 'atandi', 'yolda', 'basladi', 'tamamlandi'], cur = j.status === 'iptal' ? -1 : st.indexOf(j.status === 'faturalandi' ? 'tamamlandi' : j.status);
        var parts = (j.parts_used || []).map(function (x) { return esc((x.name || '') + ' × ' + (x.qty || x.quantity || 1)); }).join(', ') || '—';
        h += '<div class="spx-card"><b>' + esc(j.job_number || '') + ' — ' + esc(j.customer_name || '') + '</b>' +
          '<div style="display:flex;gap:4px;margin:10px 0">' + st.map(function (k, i) { return '<div style="flex:1;text-align:center;font-size:12px;font-weight:700;color:' + (i <= cur ? '#15803d' : '#94a3b8') + '"><div style="height:6px;border-radius:9px;background:' + (i <= cur ? '#16a34a' : '#e2e8f0') + ';margin-bottom:4px"></div>' + FST[k] + '</div>'; }).join('') + '</div>' +
          (j.status === 'iptal' ? '<p style="color:#b91c1c"><b>İptal edildi:</b> ' + esc(j.cancel_reason || '') + '</p>' : '') +
          '<div class="spx-g"><div><small>Müşteri</small><br>' + esc(j.customer_name || '') + ' · ' + esc(j.customer_phone || '') + '<br>' + esc(j.customer_address || '') + '</div><div><small>Cihaz</small><br>' + esc((j.device_brand_name || '') + ' ' + (j.device_type || '') + ' ' + (j.device_model || '')) + '</div><div><small>Arıza</small><br>' + esc(j.fault_description || '—') + '</div><div><small>Yapılan işlem</small><br>' + esc(j.work_done || '—') + '</div><div><small>Parçalar</small><br>' + parts + '</div><div><small>İşçilik / Toplam</small><br>' + money(j.labor_fee || 0) + ' / <b>' + money(j.total_amount || 0) + '</b></div><div><small>İmzalar</small><br>Müşteri: ' + (j.has_customer_signature ? '✔' : '—') + ' · Teknisyen: ' + (j.has_tech_signature ? '✔' : '—') + '</div><div><small>Fotoğraf</small><br>Önce ' + (j.photos_before || []).length + ' · Sonra ' + (j.photos_after || []).length + '</div><div><small>Açılış</small><br>' + fmD(j.created_at) + '</div><div><small>Başlangıç</small><br>' + fmD(j.started_at) + '</div><div><small>Tamamlanma</small><br>' + fmD(j.completed_at) + '</div></div></div>';
      }
      box.innerHTML = h; $('#fm_jx').onclick = function () { FM.job = ''; fmJobs(fid); };
    }).catch(function (e) { box.innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  /* ===== Firma modu: firma girişinde sade ekran, kendi logo/adı, manuel servis ekleme ===== */
  var FIRM = null, FFRESH = false, FIRMBUSY = false, FTOK = '', FLOGO = '', FLOGOBUSY = false, FHID = {};
  (function () { try { var s = JSON.parse(localStorage.getItem('spx_firm') || 'null'); if (s && s.tok && s.tok === localStorage.getItem('token')) { FTOK = s.tok; FIRM = { name: s.name, has_logo: s.has_logo, phone: s.phone || '', address: s.address || '' }; FLOGO = (s.logo && s.logo.indexOf('data:image/png') === 0) ? s.logo : ''; } } catch (e) { } })();
  function firmSave() { try { localStorage.setItem('spx_firm', JSON.stringify(FIRM ? { tok: FTOK, name: FIRM.name, has_logo: FIRM.has_logo, phone: FIRM.phone || '', address: FIRM.address || '', logo: FLOGO.indexOf('data:') === 0 ? FLOGO : '' } : null)); } catch (e) { } }
  (function () {
    var s = document.createElement('style');
    s.textContent = 'body.spx-firm nav a[data-testid=tab-announcements],body.spx-firm nav a[data-testid=tab-balance],body.spx-firm nav a[data-testid=tab-more],body.spx-firm nav a[data-testid=tab-chat],body.spx-firm nav a[data-spx-fh],body.spx-firm #spx-score,body.spx-firm #spx-sc,body.spx-firm #spx-pwa,body.spx-firm #spx-pwa-card{display:none!important}' +
      '#spx-fbar{display:none}@media(max-width:1023px){body.spx-fbar-on nav.fixed.bottom-0{display:none!important}body.spx-firm #spx-fbar{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:9995;background:#fff;border-top:1px solid #e2e8f0;padding:4px 2px calc(4px + env(safe-area-inset-bottom));box-shadow:0 -2px 10px rgba(0,0,0,.06)}#spx-fbar button{flex:1 1 0;min-width:0;border:0;background:none;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;padding:5px 0;color:#334155;cursor:pointer}body.spx-firm main{padding-bottom:84px!important}body.spx-firm #spx-ffab{display:none!important}}' +
      '@media(max-width:1023px){body.spx-firm nav.fixed.bottom-0>div{display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;grid-template-columns:none!important;justify-content:space-around!important}body.spx-firm nav.fixed.bottom-0 a[data-testid^=tab-],body.spx-firm nav.fixed.bottom-0 a[id^=spx-fb-]{flex:1 1 0!important;min-width:0!important;width:auto!important;display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;font-size:11px!important;gap:2px;padding:6px 2px!important;position:relative}body.spx-firm nav.fixed.bottom-0 a[data-spx-fh]{display:none!important}body.spx-firm nav.fixed.bottom-0 [data-spx-fbw]{flex:1 1 0!important;min-width:0!important}}' +
      '#spx-ffab{position:fixed;right:14px;bottom:84px;z-index:9990;border:0;border-radius:99px;background:#0E9AA7;color:#fff;font-weight:700;font-size:15px;padding:13px 18px;box-shadow:0 6px 18px rgba(0,0,0,.25);cursor:pointer}' +
      '@media(min-width:1024px){#spx-ffab{bottom:24px}}' +
      '#spx-fm{position:fixed;inset:0;z-index:99990;background:rgba(15,23,42,.55);display:flex;align-items:flex-end;justify-content:center}' +
      '#spx-fm>div{box-sizing:border-box;background:#fff;width:100%;max-width:520px;max-height:92vh;overflow:auto;border-radius:18px 18px 0 0;padding:16px}' +
      '@media(min-width:640px){#spx-fm{align-items:center}#spx-fm>div{border-radius:18px}}' +
      '@media(max-width:1023px){body.spx-fbar-on #spx-fm{top:0;bottom:calc(64px + env(safe-area-inset-bottom));align-items:stretch;background:#fff}body.spx-fbar-on #spx-fm>div{box-sizing:border-box;max-width:none!important;width:100%;max-height:none;height:100%;border-radius:0;padding:16px 16px 24px}}' +
      '#spx-fm label{display:block;font-size:12px;font-weight:600;color:#475569;margin-top:10px}#spx-fm input,#spx-fm select,#spx-fm textarea{width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:10px;padding:10px;font-size:15px;margin-top:3px;background:#fff;color:#0f172a}';
    document.head.appendChild(s);
  })();
  /* PDF üretimi (jsPDF) logoyu PNG bekler; JPEG/WEBP verilirse PDF hiç oluşmaz → her zaman PNG'ye çevir (en fazla 600 px) */
  function firmPng(d) {
    return new Promise(function (res) {
      var im = new Image(); im.onload = function () {
        try { var k = Math.min(1, 600 / Math.max(im.width, im.height)), c = document.createElement('canvas'); c.width = Math.max(1, Math.round(im.width * k)); c.height = Math.max(1, Math.round(im.height * k)); c.getContext('2d').drawImage(im, 0, 0, c.width, c.height); res(c.toDataURL('image/png')); } catch (e) { res(''); }
      }; im.onerror = function () { res(''); }; im.src = d;
    });
  }
  function firmLogoLoad() {
    if (FLOGO || FLOGOBUSY || !FIRM || !FIRM.has_logo) return; FLOGOBUSY = true;
    fetch(location.origin + '/api/firm/logo', { headers: { Authorization: 'Bearer ' + LS.get('token', '') } }).then(function (r) { return r.ok ? r.blob() : null; }).then(function (b) { return b ? new Promise(function (res) { var fr = new FileReader(); fr.onload = function () { res(fr.result); }; fr.readAsDataURL(b); }) : ''; }).then(function (d) { return d ? firmPng(d) : ''; }).then(function (d) { if (d) { FLOGO = d; firmSave(); } }).catch(function () { }).then(function () { FLOGOBUSY = false; });
  }
  function firmBrand() {
    var nm = FIRM.name || 'Firma';
    var nodes = document.querySelectorAll('header *, nav *, aside *, main h1, main h2, body > div > div:first-child a'), shown = 0;
    for (var i = 0; i < nodes.length; i++) {
      var e = nodes[i];
      if (e.id === 'spx-ffab' || e.closest('#spx-fm')) continue;
      if (e.tagName === 'IMG' && /logo|servisplus/i.test(e.getAttribute('src') || '') && !e.getAttribute('data-spx-fl')) {
        if (FLOGO) { e.setAttribute('data-spx-fl', '1'); e.src = FLOGO; e.removeAttribute('srcset'); e.style.objectFit = 'contain'; }
        else if (!FIRM.has_logo) { var sp = document.createElement('span'); sp.textContent = nm; sp.setAttribute('data-spx-fn', '1'); sp.style.cssText = 'font-weight:800;font-size:16px;color:#0f172a'; e.replaceWith(sp); }
      } else if (e.children.length === 0 && /^servis\s*plus(\s+usta)?$/i.test((e.textContent || '').trim())) { e.textContent = nm; e.setAttribute('data-spx-fn', '1'); }
    }
    /* firma adı ekranda tek kez görünsün: ilk görünür olan kalır, tekrarları gizlenir */
    var all = document.querySelectorAll('[data-spx-fn]'), seen = 0;
    for (var k = 0; k < all.length; k++) { var el = all[k]; if (el.offsetParent === null && getComputedStyle(el).display !== 'none') continue; if (el.style.display === 'none' && el.getAttribute('data-spx-dup')) continue; if (!seen) { seen = 1; continue; } el.style.display = 'none'; el.setAttribute('data-spx-dup', '1'); }
    if (/servis\s*plus/i.test(document.title)) document.title = document.title.replace(/servis\s*plus(\s+usta)?/ig, nm);
  }
  function firmMode() {
    var tok = LS.get('token', '');
    if (tok !== FTOK) { FTOK = tok; FIRM = null; FFRESH = false; FLOGO = ''; document.body.classList.remove('spx-firm', 'spx-fbar-on'); var fb1 = document.getElementById('spx-fbar'); if (fb1) fb1.remove(); var f0 = document.getElementById('spx-ffab'); if (f0) f0.remove(); }
    var tech = document.body.classList.contains('spx-tech');
    if (!tech || !tok) { var fb0 = document.getElementById('spx-fbar'); if (fb0) fb0.remove(); document.body.classList.remove('spx-fbar-on', 'spx-firm'); return; }
    if (FIRM === null) {
      if (!FIRMBUSY) { FIRMBUSY = true; pcall('GET', '/firm/me').then(function (r) { FIRM = (r && r.firm) ? r.firm : false; firmSave(); }).catch(function () { FIRM = false; }).then(function () { FIRMBUSY = false; }); }
      return;
    }
    document.body.classList.toggle('spx-firm', !!FIRM);
    if (!FIRM) return;
    if (!FFRESH && !FIRMBUSY) { FIRMBUSY = true; pcall('GET', '/firm/me').then(function (r) { if (r && r.firm) { var o = FIRM; FIRM = r.firm; FIRM.sub = !!r.firm.sub; if (o && o.name !== FIRM.name) firmSave(); } FFRESH = true; }).catch(function () { }).then(function () { FIRMBUSY = false; }); }
    firmLogoLoad();
    var links = document.querySelectorAll('nav a');
    for (var i = 0; i < links.length; i++) {
      var a = links[i], t = (a.textContent || '').trim();
      if (/^(Sohbet|Duyuru|Duyurular|Bakiyem|Daha)\b/i.test(t) || /^tab-(announcements|balance|more|chat)$/.test(a.getAttribute('data-testid') || '')) { a.setAttribute('data-spx-fh', '1'); var h = a.getAttribute('href'); if (h && h.length > 5) FHID[h] = 1; }
    }
    var p = location.pathname.replace(/\/$/, '');
    if (FHID[p] || /^\/tech\/(chat|sohbet|announcements|duyuru|balance|more|daha)(\/|$)/.test(p)) { location.replace('/tech'); return; }
    firmBrand();
    firmBar(); firmHideBlocks(); firmNames();
    var gt = ''; try { gt = sessionStorage.getItem('spx_gotab') || ''; } catch (e) { }
    if (gt && /^\/tech\/?$/.test(location.pathname) && firmTab(gt)) { try { sessionStorage.removeItem('spx_gotab'); } catch (e) { } }
    var on = /^\/tech\/?$/.test(location.pathname), fab = document.getElementById('spx-ffab');
    if (on && !fab) { fab = document.createElement('button'); fab.id = 'spx-ffab'; fab.textContent = '＋ Manuel servis ekle'; fab.onclick = firmNewJob; document.body.appendChild(fab); }
    else if (!on && fab) fab.remove();
  }
  function firmTxt(s) {
    if (!FIRM) return s;
    s = String(s).replace(/(^|[^.\w\/@])servis\s*plus(\s+usta)?(?![\w.])/ig, function (m, a) { return a + (FIRM.name || ''); });
    s = s.replace(/0?\s?544[\s-]?444[\s-]?4[\s-]?004|0?850[\s\d]{7,10}/g, FIRM.phone || '');
    return s;
  }
  function firmWaUrl(u) {
    try { u = String(u); if (!/(wa\.me|whatsapp\.com)/i.test(u)) return u; var i = u.indexOf('text='); if (i < 0) return u; var j = u.indexOf('&', i), tx = decodeURIComponent(u.slice(i + 5, j < 0 ? undefined : j).replace(/\+/g, ' ')); return u.slice(0, i + 5) + encodeURIComponent(firmTxt(tx)) + (j < 0 ? '' : u.slice(j)); } catch (e) { return u; }
  }
  (function () {
    var wo = window.open; window.open = function (u) { var a = Array.prototype.slice.call(arguments); if (FIRM && u) a[0] = firmWaUrl(u); return wo.apply(window, a); };
    document.addEventListener('click', function (e) { var a = e.target.closest && e.target.closest('a[href]'); if (!a || !FIRM) return; var h = a.getAttribute('href') || ''; if (/(wa\.me|whatsapp\.com)/i.test(h)) { var n = firmWaUrl(h); if (n !== h) a.setAttribute('href', n); } }, true);
  })();
  /* firma hesabında ServisPlus görselleri (PDF alt logosu vb.) firmanın kendi logosuna çevrilir; yoksa şeffaf piksel */
  var PIX = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4//8/AAX+Av4N70a4AAAAAElFTkSuQmCC';
  function firmImgUrl(u) { try { var s = String(u); if (FIRM && /(\/brand\/|logo-servisplus|servisplus\.net\.tr\/images\/logo|footer-logo)/i.test(s) && !/brand-logo/.test(s)) return FLOGO || PIX; } catch (e) { } return u; }
  (function () {
    try {
      var d = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');
      if (d && d.set) Object.defineProperty(HTMLImageElement.prototype, 'src', { configurable: true, enumerable: d.enumerable, get: d.get, set: function (v) { d.set.call(this, firmImgUrl(v)); } });
      var sa = Element.prototype.setAttribute; Element.prototype.setAttribute = function (k, v) { if (this.tagName === 'IMG' && k === 'src') v = firmImgUrl(v); return sa.call(this, k, v); };
      var of = window.fetch; window.fetch = function (u, o) { var s = typeof u === 'string' ? u : (u && u.url) || ''; var n = firmImgUrl(s); if (n !== s) return of.call(window, n, o); return of.apply(window, arguments); };
    } catch (e) { }
  })();
  /* firma adı ekranda yalnız logonun yanında kalsın: üst çubuktaki kullanıcı adı ve "Hoş geldin" başlığındaki ad gizlenir */
  function firmNames() {
    var lc = function (s) { return (s || '').trim().replace(/\s+/g, ' ').toLocaleLowerCase('tr'); };
    var nm = [lc(FIRM.name), lc(FIRM.contact_name)].filter(Boolean), hd = document.querySelector('header'), bc = null, i, e;
    var scope = document.querySelectorAll('header *, main *');
    for (i = 0; i < scope.length; i++) { e = scope[i]; if (e.children.length === 0 && /^usta paneli$/i.test((e.textContent || '').trim())) { bc = e.parentElement; break; } }
    for (i = 0; i < scope.length; i++) {
      e = scope[i]; if (e.children.length || e.getAttribute('data-spx-nm') || (bc && bc.contains(e))) continue;
      if (nm.indexOf(lc(e.textContent)) < 0) continue;
      var inHd = hd && hd.contains(e), r = e.getBoundingClientRect();
      if (inHd || (r.top < 320 && r.top > -50)) { e.setAttribute('data-spx-nm', '1'); e.style.setProperty('display', 'none', 'important'); }
    }
  }
  function firmHideBlocks() {
    var mn = document.querySelector('main'); if (!mn) return;
    var pats = [/^Arıza Asistan/i, /^Müşteriye (mesaj|bildir)/i], els = mn.querySelectorAll('h1,h2,h3,h4,p,span,div,button,a');
    for (var i = 0; i < els.length; i++) {
      var e = els[i]; if (e.children.length > 2 || e.closest('[data-spx-fhb]') || e.closest('#spx-fm') || e.closest('[role=dialog],[class*=modal],[class*=Modal]')) continue;
      var tx = (e.textContent || '').trim(); if (tx.length > 40 || !pats.some(function (r) { return r.test(tx); })) continue;
      var c = e, k = 0; while (c.parentElement && c.parentElement !== mn && k < 4 && !(c.tagName === 'SECTION' || /rounded|border|card/.test(c.className || ''))) { c = c.parentElement; k++; }
      c.setAttribute('data-spx-fhb', '1'); c.style.setProperty('display', 'none', 'important');
    }
  }
  function firmPress(el) {
    try { ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(function (n) { var C = /^pointer/.test(n) && window.PointerEvent ? PointerEvent : MouseEvent; el.dispatchEvent(new C(n, { bubbles: true, cancelable: true, button: 0, view: window })); }); } catch (e) { el.click(); }
  }
  function firmTab(label) {
    var tabs = document.querySelectorAll('[role=tab]');
    for (var i = 0; i < tabs.length; i++) { if (new RegExp('^' + label, 'i').test((tabs[i].textContent || '').trim())) { firmPress(tabs[i]); return true; } }
    return false;
  }
  function firmGo(label) {
    if (/^\/tech\/?$/.test(location.pathname)) { if (firmTab(label)) return; }
    try { sessionStorage.setItem('spx_gotab', label); } catch (e) { }
    location.href = '/tech';
  }
  function firmNavGo(id, fb) { var a = document.querySelector('nav a[data-testid=' + id + ']'); if (a) a.click(); else if (fb) location.href = fb; }
  function firmBar() {
    var bar = document.getElementById('spx-fbar');
    if (bar) { if (!bar.parentNode) document.body.appendChild(bar); document.body.classList.add('spx-fbar-on'); return; }
    bar = document.createElement('div'); bar.id = 'spx-fbar'; bar.className = 'notranslate';
    var it = [['📋', 'Görevler', function () { firmNavGo('tab-jobs', '/tech'); }], ['📝', 'Teklif', function () { firmNavGo('tab-quotes'); }], ['＋', 'Yeni', firmNewJob], ['🔧', 'Bakım', firmViewMaint, 'b'], ['☰', 'Daha', function () { firmInfo(); }]];
    it.forEach(function (d) {
      if (d[1] === 'Teklif' && !document.querySelector('nav a[data-testid=tab-quotes]')) return;
      var ff = (getComputedStyle(document.body).fontFamily || 'sans-serif').replace(/"/g, "'");
      var b = document.createElement('button'); b.type = 'button'; b.onclick = function () { var op = document.getElementById('spx-fm'); if (op) op.remove(); var rv = document.getElementById('spx-rcv'); if (rv) rv.remove(); d[2](); };
      b.style.cssText = 'flex:1 1 0;min-width:0;height:54px;border:0;background:none;margin:0;padding:4px 0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;cursor:pointer;font-family:' + ff + ';color:#334155';
      var ic = document.createElement('div'); ic.textContent = d[0]; ic.style.cssText = 'display:block;height:24px;line-height:24px;font-size:20px;font-family:' + ff + ';margin:0;padding:0';
      var lb = document.createElement('div'); lb.textContent = d[1]; lb.style.cssText = 'display:block;height:14px;line-height:14px;font-size:11px;font-weight:600;font-family:' + ff + ';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;margin:0;padding:0';
      b.appendChild(ic); b.appendChild(lb); if (d[3] === 'b') { var bg = document.createElement('i'); bg.id = 'spx-mtb'; bg.style.display = 'none'; b.appendChild(bg); } bar.appendChild(b);
    });
    document.body.appendChild(bar); document.body.classList.add('spx-fbar-on'); firmBadge();
  }
  /* sitenin kendi "Daha" sekmesine/yoluna basılırsa eski sayfa yerine firma menüsü açılır */
  document.addEventListener('click', function (e) { if (!FIRM) return; var a = e.target.closest && e.target.closest('a'); if (!a) return; var tid = a.getAttribute('data-testid') || '', h = a.getAttribute('href') || ''; if (tid === 'tab-more' || /\/tech\/more\/?$/.test(h)) { e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation(); firmInfo(); } }, true);
  /* ===== "Daha": firma menüsü (düğmeler) → Firma bilgileri / Şifre / Kullanıcılar / PDF alt metni / Ciro raporu ===== */
  function fmShell(wide) {
    var old = document.getElementById('spx-fm'); if (old) old.remove();
    var m = document.createElement('div'); m.id = 'spx-fm'; m.innerHTML = '<div' + (wide ? ' style="max-width:760px"' : '') + '>Yükleniyor…</div>'; document.body.appendChild(m);
    var hd = document.querySelector('header'); if (hd && window.innerWidth < 1024 && document.body.classList.contains('spx-fbar-on')) m.style.top = Math.max(0, Math.round(hd.getBoundingClientRect().bottom)) + 'px';   /* üst logo görünür kalsın */
    m.onclick = function (e) { if (e.target === m) m.remove(); }; return m;
  }
  function fmHead(title, back) { return '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">' + (back ? '<button id="fi-b" style="border:0;background:#f1f5f9;border-radius:9px;padding:6px 11px;font-size:15px;cursor:pointer">‹</button>' : '') + '<b style="font-size:18px;flex:1">' + title + '</b><button id="fi-x" style="border:0;background:none;font-size:26px;cursor:pointer">×</button></div>'; }
  var FB = 'width:100%;border:0;border-radius:12px;background:#0E9AA7;color:#fff;font-weight:700;font-size:16px;padding:13px;margin-top:14px;cursor:pointer';
  function fmBind(m) { var x = document.getElementById('fi-x'); if (x) x.onclick = function () { m.remove(); }; var b = document.getElementById('fi-b'); if (b) b.onclick = firmInfo; }
  function fmV(id) { return document.getElementById(id).value.trim(); }
  function firmInfo() {
    var m = fmShell(false), mi = function (ic, t, s, id) { return '<button id="' + id + '" style="display:flex;align-items:center;gap:12px;width:100%;text-align:left;border:1px solid #e2e8f0;background:#fff;border-radius:14px;padding:13px;margin-top:9px;cursor:pointer;color:#0f172a"><span style="font-size:22px;width:30px;text-align:center">' + ic + '</span><span style="flex:1"><b style="display:block;font-size:15px">' + t + '</b><small style="color:#64748b">' + s + '</small></span><span style="color:#94a3b8;font-size:20px">›</span></button>'; };
    m.firstChild.innerHTML = fmHead('Daha', false) +
      mi('🏢', 'Firma bilgileri', 'Ad, telefon, adres, vergi, logo', 'fm-i1') + mi('📈', 'Aylık ciro raporu', 'Aylık ve toplam kazanç', 'fm-i2') + (FIRM && FIRM.sub ? '' : mi('💰', 'Kasa hareketleri', 'Gelir ve gider kayıtları', 'fm-k1') + mi('📦', 'Stok yönetimi', 'Ürün, giriş ve çıkış', 'fm-k2')) + mi('📄', 'PDF alt metni', 'Servis fişinin alt yazısı', 'fm-i3') +
      mi('👥', 'Kullanıcılar ve iş atama', 'En fazla 3 ek kullanıcı', 'fm-i4') + mi('🔑', 'Şifre değiştir', 'Giriş şifrenizi yenileyin', 'fm-i5') +
      '<button id="fm-i6" style="width:100%;margin-top:14px;border:1px solid #fecaca;border-radius:12px;background:#fff;color:#b91c1c;font-weight:700;font-size:15px;padding:12px;cursor:pointer">Çıkış yap</button>';
    fmBind(m);
    document.getElementById('fm-i1').onclick = firmViewInfo; document.getElementById('fm-i2').onclick = firmViewReport; document.getElementById('fm-i3').onclick = firmViewPdf;
    var k1 = document.getElementById('fm-k1'), k2 = document.getElementById('fm-k2'); if (k1) k1.onclick = firmViewCash; if (k2) k2.onclick = firmViewStock;
    document.getElementById('fm-i4').onclick = firmViewUsers; document.getElementById('fm-i5').onclick = firmViewPass;
    document.getElementById('fm-i6').onclick = function () { try { localStorage.removeItem('token'); localStorage.removeItem('spx_firm'); } catch (e) { } location.href = '/login'; };
  }
  function firmSaved(b, lg) { if (FIRM) { if (b.name) FIRM.name = b.name; if (b.phone != null) FIRM.phone = b.phone; if (b.address != null) FIRM.address = b.address; if (lg) { FIRM.has_logo = true; firmPng(lg).then(function (d) { if (d) { FLOGO = d; firmSave(); } }); } firmSave(); } }
  function firmViewInfo() {
    var m = fmShell(false);
    pcall('GET', '/firm/me').then(function (r) {
      var f = r.firm || {}, E = function (s) { return esc(s || ''); }, ro = 'disabled style="background:#f1f5f9;color:#475569"';
      m.firstChild.innerHTML = fmHead('Firma bilgileri', true) + '<small style="color:#64748b;display:block">Servis fişi, QR etiket ve WhatsApp mesajlarında kullanılır. Firma adı, telefon, adres ve logo değişikliği için yönetici ile görüşün; yalnızca vergi bilgilerini siz düzenleyebilirsiniz.</small>' +
        '<label>Firma adı<input value="' + E(f.name) + '" ' + ro + '></label><label>Yetkili<input value="' + E(f.contact_name) + '" ' + ro + '></label>' +
        '<label>Telefon<input value="' + E(f.phone) + '" ' + ro + '></label><label>Adres<input value="' + E(f.address) + '" ' + ro + '></label>' +
        '<div style="display:flex;gap:8px"><label style="flex:1">Vergi no<input id="fi-v" value="' + E(f.tax_no) + '"></label><label style="flex:1">Vergi dairesi<input id="fi-vd" value="' + E(f.tax_office) + '"></label></div>' +
        '<label>Kullanıcı adı<input value="' + E(f.login_email) + '" ' + ro + '></label><button id="fi-go" style="' + FB + '">Vergi bilgilerini kaydet</button>';
      fmBind(m);
      document.getElementById('fi-go').onclick = function () {
        var btn = this; btn.disabled = true;
        pcall('PUT', '/firm/me', { tax_no: fmV('fi-v'), tax_office: fmV('fi-vd') }).then(function (r) { toast(r.changed && r.changed.length ? 'Kaydedildi' : 'Değişiklik yok'); firmInfo(); }).catch(function (e) { btn.disabled = false; toast(e.message || 'Kaydedilemedi'); });
      };
    }).catch(function (e) { m.remove(); toast(e.message || 'Yüklenemedi'); });
  }
  function firmViewPass() {
    var m = fmShell(false);
    m.firstChild.innerHTML = fmHead('Şifre değiştir', true) + '<label>Mevcut şifre<input id="fi-p0" type="password" autocomplete="current-password"></label><label>Yeni şifre (en az 8 karakter)<input id="fi-p1" type="password" autocomplete="new-password"></label><label>Yeni şifre (tekrar)<input id="fi-p2" type="password" autocomplete="new-password"></label><button id="fi-go" style="' + FB + '">Şifreyi değiştir</button>';
    fmBind(m);
    document.getElementById('fi-go').onclick = function () {
      var a = document.getElementById('fi-p1').value; if (a !== document.getElementById('fi-p2').value) { toast('Yeni şifreler aynı değil'); return; }
      var btn = this; btn.disabled = true;
      pcall('PUT', '/firm/me', { current_password: document.getElementById('fi-p0').value, new_password: a }).then(function () { toast('Şifre değiştirildi'); firmInfo(); }).catch(function (e) { btn.disabled = false; toast(e.message || 'Değiştirilemedi'); });
    };
  }
  function firmViewUsers() {
    var m = fmShell(false);
    var draw = function () {
      ASG.users = null;
      pcall('GET', '/firm/users').then(function (r) {
        var h = fmHead('Kullanıcılar', true) + '<small style="color:#64748b;display:block;margin-bottom:6px">Ana hesaba ek en fazla ' + r.max + ' kullanıcı. Yönetici tüm işleri görür ve iş detayından kullanıcıya iş atar; eklenen kullanıcılar yalnızca kendilerine atanan (veya kendi açtıkları) işleri görür.</small>' +
          '<div style="padding:8px 0;border-bottom:1px solid #eef2f6"><b>Ana hesap</b> <small style="color:#64748b">' + esc(r.owner || '') + '</small></div>' +
          (r.users || []).map(function (u) { return '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #eef2f6"><span>' + esc(u.name || '') + ' <small style="color:#64748b">' + esc(u.email) + '</small>' + (u.active === false ? ' <small style="color:#b91c1c">(kapalı)</small>' : '') + '</span>' + (r.can_manage ? '<button data-ud="' + u.id + '" style="border:1px solid #fecaca;background:#fff;color:#b91c1c;border-radius:8px;padding:5px 11px;cursor:pointer">Sil</button>' : '') + '</div>'; }).join('');
        if (r.can_manage && (r.users || []).length < r.max) h += '<div style="margin-top:10px"><b>Yeni kullanıcı</b><input id="fu-n" placeholder="Ad soyad" style="margin-top:6px"><input id="fu-e" type="email" placeholder="Kullanıcı adı (e-posta)" style="margin-top:6px"><input id="fu-p" type="text" placeholder="Şifre (en az 8)" style="margin-top:6px"><button id="fu-go" style="' + FB + '">Kullanıcı ekle (' + (r.users || []).length + '/' + r.max + ')</button></div>';
        else if (!r.can_manage) h += '<small style="color:#64748b;display:block;margin-top:8px">Kullanıcı eklemeyi yalnızca ana hesap yapabilir.</small>';
        m.firstChild.innerHTML = h; fmBind(m);
        Array.prototype.forEach.call(m.querySelectorAll('[data-ud]'), function (b) { b.onclick = function () { if (!confirm('Kullanıcı silinsin mi?')) return; pcall('DELETE', '/firm/users/' + b.getAttribute('data-ud')).then(draw).catch(function (e) { toast(e.message); }); }; });
        var g = document.getElementById('fu-go'); if (g) g.onclick = function () { pcall('POST', '/firm/users', { name: document.getElementById('fu-n').value, email: document.getElementById('fu-e').value, password: document.getElementById('fu-p').value }).then(function () { toast('Kullanıcı eklendi'); draw(); }).catch(function (e) { toast(e.message || 'Eklenemedi'); }); };
      }).catch(function (e) { m.remove(); toast(e.message || 'Yüklenemedi'); });
    }; draw();
  }
  function firmViewPdf() {
    var m = fmShell(false);
    pcall('GET', '/firm/me').then(function (r) {
      var f = r.firm || {};
      m.firstChild.innerHTML = fmHead('PDF alt metni', true) + '<small style="color:#64748b;display:block;margin-bottom:6px">Servis fişi PDF\'inin altındaki yazı. Aşağıdaki kısa kodlar firma bilgilerinizle otomatik dolar: <b>{firma_adi}</b>, <b>{adres}</b>, <b>{telefon}</b>. ' + (f.pdf_custom ? 'Şu an <b>kendi metniniz</b> kullanılıyor.' : 'Şu an <b>ortak metin</b> kullanılıyor.') + '</small>' +
        '<textarea id="fp-t" rows="9" style="width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:10px;padding:10px;font-size:14px">' + esc(f.pdf_raw || '') + '</textarea>' +
        '<button id="fp-go" style="' + FB + '">Kaydet</button><button id="fp-rs" style="width:100%;margin-top:8px;border:1px solid #cbd5e1;border-radius:12px;background:#fff;color:#334155;font-weight:600;padding:11px;cursor:pointer">Ortak metne dön</button>';
      fmBind(m);
      document.getElementById('fp-go').onclick = function () { pcall('PUT', '/firm/pdf-note', { text: document.getElementById('fp-t').value }).then(function () { toast('PDF metni kaydedildi, sayfa yenileniyor…'); setTimeout(function () { location.reload(); }, 700); }).catch(function (e) { toast(e.message || 'Kaydedilemedi'); }); };
      document.getElementById('fp-rs').onclick = function () { if (!confirm('Kendi metniniz silinip ortak metne dönülsün mü?')) return; pcall('PUT', '/firm/pdf-note', { text: '' }).then(function () { toast('Ortak metne dönüldü, sayfa yenileniyor…'); setTimeout(function () { location.reload(); }, 700); }).catch(function (e) { toast(e.message); }); };
    }).catch(function (e) { m.remove(); toast(e.message || 'Yüklenemedi'); });
  }
  function fmReportHtml(r) {
      var TL = function (n) { return '₺' + (Math.round((n || 0) * 100) / 100).toLocaleString('tr-TR', { minimumFractionDigits: 0, maximumFractionDigits: 2 }); };
      var MN = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'], lab = function (k) { var p = k.split('-'); return MN[parseInt(p[1], 10) - 1] + ' ' + p[0].slice(2); };
      var mx = Math.max.apply(null, r.months.map(function (b) { return b.revenue; }).concat([1]));
      var chg = r.change_pct == null ? '' : '<small style="color:' + (r.change_pct >= 0 ? '#15803d' : '#b91c1c') + ';font-weight:700">' + (r.change_pct >= 0 ? '▲ ' : '▼ ') + Math.abs(r.change_pct) + '% geçen aya göre</small>';
      var card = function (t, v, s, c) { return '<div style="flex:1 1 140px;background:' + c + ';border-radius:14px;padding:12px"><small style="color:#475569;font-weight:600">' + t + '</small><div style="font-size:22px;font-weight:800;color:#0f172a;margin:2px 0">' + v + '</div>' + (s || '') + '</div>'; };
      var bars = r.months.map(function (b) { var h = Math.max(3, Math.round(b.revenue / mx * 110)), cur = b === r.months[r.months.length - 1]; return '<div style="flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:flex-end" title="' + lab(b.month) + ': ' + TL(b.revenue) + ' · ' + b.jobs + ' iş"><small style="font-size:9px;color:#64748b">' + (b.revenue ? (b.revenue >= 1000 ? Math.round(b.revenue / 100) / 10 + 'B' : Math.round(b.revenue)) : '') + '</small><div style="width:78%;height:' + h + 'px;border-radius:6px 6px 2px 2px;background:' + (cur ? 'linear-gradient(#0E9AA7,#0b7480)' : '#a5d8de') + '"></div><small style="font-size:9px;color:#64748b;margin-top:3px;white-space:nowrap">' + lab(b.month).split(' ')[0] + '</small></div>'; }).join('');
      var rowsT = r.months.slice().reverse().filter(function (b) { return b.jobs; }).map(function (b) { return '<tr><td style="padding:6px 4px">' + lab(b.month) + '</td><td style="text-align:right">' + b.jobs + '</td><td style="text-align:right">' + TL(b.parts) + '</td><td style="text-align:right">' + TL(b.labor) + '</td><td style="text-align:right;font-weight:700">' + TL(b.revenue) + '</td></tr>'; }).join('') || '<tr><td colspan="5" style="padding:12px;color:#64748b">Henüz tamamlanan iş yok.</td></tr>';
      var list = function (a, tt) { return '<div style="flex:1 1 220px"><b style="font-size:14px">' + tt + '</b>' + (a.length ? a.map(function (x) { return '<div style="display:flex;justify-content:space-between;gap:8px;padding:6px 0;border-bottom:1px solid #eef2f6;font-size:13px"><span>' + esc(x.name) + ' <small style="color:#64748b">· ' + x.jobs + ' iş</small></span><b>' + TL(x.revenue) + '</b></div>'; }).join('') : '<div style="color:#64748b;font-size:13px;padding:6px 0">Veri yok</div>') + '</div>'; };
      return '' +
        '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">' + card('Bu ay', TL(r.current.revenue), '<small style="color:#64748b">' + r.current.jobs + ' iş</small> ' + chg, '#ecfeff') + card('Geçen ay', TL(r.previous.revenue), '<small style="color:#64748b">' + r.previous.jobs + ' iş</small>', '#f1f5f9') + card('Toplam kazanç', TL(r.total.revenue), '<small style="color:#64748b">' + r.total.jobs + ' tamamlanan iş</small>', '#f0fdf4') + card('Ortalama iş', TL(r.avg_ticket), '<small style="color:#64748b">' + r.open + ' açık · ' + r.cancelled + ' iptal</small>', '#fffbeb') + '</div>' +
        '<div style="margin-top:14px"><b style="font-size:14px">Son 12 ay</b><div style="display:flex;align-items:flex-end;gap:3px;height:150px;margin-top:6px;padding:8px 4px 0;border-bottom:1px solid #cbd5e1">' + bars + '</div></div>' +
        '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px"><div style="flex:1 1 140px;border:1px solid #e2e8f0;border-radius:12px;padding:10px"><small style="color:#64748b">Parça geliri</small><div style="font-weight:800;font-size:17px">' + TL(r.total.parts) + '</div></div><div style="flex:1 1 140px;border:1px solid #e2e8f0;border-radius:12px;padding:10px"><small style="color:#64748b">İşçilik geliri</small><div style="font-weight:800;font-size:17px">' + TL(r.total.labor) + '</div></div>' + (r.best_month ? '<div style="flex:1 1 140px;border:1px solid #e2e8f0;border-radius:12px;padding:10px"><small style="color:#64748b">En iyi ay</small><div style="font-weight:800;font-size:17px">' + lab(r.best_month.month) + ' · ' + TL(r.best_month.revenue) + '</div></div>' : '') + '</div>' +
        '<div style="margin-top:14px;overflow:auto"><b style="font-size:14px">Aylık döküm</b><table style="width:100%;border-collapse:collapse;font-size:13px;margin-top:4px"><thead><tr style="color:#64748b;text-align:right"><th style="text-align:left;padding:4px">Ay</th><th>İş</th><th>Parça</th><th>İşçilik</th><th>Ciro</th></tr></thead><tbody>' + rowsT + '</tbody></table></div>' +
        '<div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:14px">' + list(r.devices, 'Cihaza göre') + list(r.customers, 'En çok iş yapılan müşteriler') + '</div>' +
        '<small style="color:#64748b;display:block;margin-top:10px">Ciro, tamamlanan ve faturalanan işlerin toplam tutarıdır; aylar işin tamamlanma tarihine göre ayrılır.</small>';
  }
  function firmViewReport() {
    var m = fmShell(true);
    pcall('GET', '/firm/report?months=12').then(function (r) {
      m.firstChild.innerHTML = fmHead('Aylık ciro raporu', true) + fmReportHtml(r);
      fmBind(m);
    }).catch(function (e) { m.remove(); toast(e.message || 'Rapor alınamadı'); });
  }
  /* ===== Firma modülleri: Bakım hatırlatma, Kasa, Stok, iş atama, web (bilgisayar) kenar menüsü ===== */
  var MT_DUE = 0, MT_BUSY = false, MT_LAST = 0;
  function fmDt(s) { if (!s) return '—'; var p = String(s).slice(0, 10).split('-'); return p.length === 3 ? p[2] + '.' + p[1] + '.' + p[0] : esc(String(s)); }
  function fmTL(n) { return '₺' + (Math.round((n || 0) * 100) / 100).toLocaleString('tr-TR', { minimumFractionDigits: 0, maximumFractionDigits: 2 }); }
  function fmPlus(d, n) { var p = (d || new Date().toISOString().slice(0, 10)).split('-'), t = +p[0] * 12 + (+p[1] - 1) + n, y = Math.floor(t / 12), mo = t % 12 + 1, dd = Math.min(+p[2], new Date(y, mo, 0).getDate()); return y + '-' + ('0' + mo).slice(-2) + '-' + ('0' + dd).slice(-2); }
  function fmWaPhone(p) { var d = String(p || '').replace(/\D/g, ''); if (d.indexOf('00') === 0) d = d.slice(2); if (d.charAt(0) === '0') d = '90' + d.slice(1); else if (d.length === 10 && d.charAt(0) === '5') d = '90' + d; return d; }
  var MT_DEF = 'Merhaba {ad}, {firma} olarak hatırlatmak isteriz: kombinizin yıllık bakım zamanı geldi ({tarih}). Randevu için bize ulaşabilirsiniz. {telefon}';
  function mtMsg() { var t = ''; try { t = localStorage.getItem('spx_mt_msg') || ''; } catch (e) { } return t || MT_DEF; }
  function mtText(r) { return mtMsg().replace(/\{ad\}/g, (r.name || '').trim()).replace(/\{firma\}/g, (FIRM && FIRM.name) || '').replace(/\{telefon\}/g, (FIRM && FIRM.phone) || '').replace(/\{tarih\}/g, fmDt(r.next_date)).replace(/\s+$/, ''); }
  function firmBadge() {
    ['spx-mtb', 'spx-mtb2'].forEach(function (id) {
      var b = document.getElementById(id); if (!b) return;
      b.textContent = MT_DUE > 99 ? '99+' : String(MT_DUE); b.style.display = MT_DUE > 0 ? 'inline-block' : 'none';
    });
  }
  function firmMaintPoll() {
    if (!FIRM || MT_BUSY || Date.now() - MT_LAST < 60000) return;
    MT_BUSY = true; MT_LAST = Date.now();
    pcall('GET', '/firm/maint').then(function (r) {
      MT_DUE = r.due || 0; firmBadge();
      var k = new Date().toISOString().slice(0, 10), seen = ''; try { seen = localStorage.getItem('spx_mt_seen') || ''; } catch (e) { }
      if (MT_DUE > 0 && seen !== k) { try { localStorage.setItem('spx_mt_seen', k); } catch (e) { } toast('🔧 ' + MT_DUE + ' müşterinin kombi bakım zamanı geldi'); }
    }).catch(function () { }).then(function () { MT_BUSY = false; });
  }
  function firmViewMaint() {
    var m = fmShell(true), flt = 'all', data = null;
    var chip = function (k, t) { return '<button data-f="' + k + '" style="border:1px solid ' + (flt === k ? '#0E9AA7' : '#cbd5e1') + ';background:' + (flt === k ? '#ecfeff' : '#fff') + ';border-radius:99px;padding:5px 12px;font-weight:700;font-size:12px;cursor:pointer;margin-right:5px">' + t + '</button>'; };
    var form = function (r) {
      r = r || {}; var iv = r.interval_months || 12;
      m.firstChild.innerHTML = fmHead(r.id ? 'Bakım kaydını düzenle' : 'Yeni bakım kaydı', false).replace('<button id="fi-x"', '<button id="mt-back" style="border:0;background:#f1f5f9;border-radius:9px;padding:6px 11px;cursor:pointer;margin-right:6px">‹ Liste</button><button id="fi-x"') +
        '<label>Müşteri adı soyadı *<input id="mt-n" value="' + esc(r.name || '') + '"></label><label>Telefon (WhatsApp için)<input id="mt-p" type="tel" value="' + esc(r.phone || '') + '" placeholder="05xx xxx xx xx"></label>' +
        '<label>Adres<input id="mt-a" value="' + esc(r.address || '') + '"></label><label>Kombi markası / modeli<input id="mt-d" value="' + esc(r.device || '') + '"></label>' +
        '<div style="display:flex;gap:8px"><label style="flex:1">Son bakım tarihi<input id="mt-l" type="date" value="' + esc(r.last_date || '') + '"></label><label style="flex:1">Bakım aralığı<select id="mt-i"><option value="6"' + (iv === 6 ? ' selected' : '') + '>6 ay</option><option value="12"' + (iv === 12 ? ' selected' : '') + '>1 yıl</option><option value="24"' + (iv === 24 ? ' selected' : '') + '>2 yıl</option></select></label></div>' +
        '<label>Sonraki bakım tarihi *<input id="mt-x" type="date" value="' + esc(r.next_date || fmPlus(r.last_date, iv)) + '"></label><small style="color:#64748b">Son bakım veya aralığı değiştirince sonraki tarih otomatik hesaplanır; isterseniz elle düzeltebilirsiniz.</small>' +
        '<label>Not<textarea id="mt-t" rows="2">' + esc(r.note || '') + '</textarea></label><button id="mt-go" style="' + FB + '">Kaydet</button>';
      fmBind(m); document.getElementById('mt-back').onclick = list;
      var auto = function () { document.getElementById('mt-x').value = fmPlus(document.getElementById('mt-l').value, +document.getElementById('mt-i').value); };
      document.getElementById('mt-l').onchange = auto; document.getElementById('mt-i').onchange = auto;
      document.getElementById('mt-go').onclick = function () {
        var btn = this, b = { name: fmV('mt-n'), phone: fmV('mt-p'), address: fmV('mt-a'), device: fmV('mt-d'), last_date: fmV('mt-l'), next_date: fmV('mt-x'), interval_months: +document.getElementById('mt-i').value, note: fmV('mt-t') };
        if (!b.name || !b.next_date) { toast('Müşteri adı ve sonraki bakım tarihi gerekli'); return; }
        btn.disabled = true; pcall(r.id ? 'PUT' : 'POST', '/firm/maint' + (r.id ? '/' + r.id : ''), b).then(function () { toast('Kaydedildi'); MT_LAST = 0; list(); }).catch(function (e) { btn.disabled = false; toast(e.message || 'Kaydedilemedi'); });
      };
    };
    var list = function () {
      pcall('GET', '/firm/maint').then(function (r) {
        data = r; MT_DUE = r.due || 0; firmBadge();
        var t = new Date().toISOString().slice(0, 10), items = r.items.filter(function (x) { return flt === 'all' ? true : (flt === 'due' ? x.next_date <= t : (x.days_left >= 0 && x.days_left <= 7)); });
        var pill = function (x) { var d = x.days_left; return d < 0 ? ['#fee2e2', '#b91c1c', -d + ' gün gecikti'] : (d === 0 ? ['#fef3c7', '#b45309', 'Bugün'] : (d <= 7 ? ['#fef3c7', '#b45309', d + ' gün kaldı'] : ['#dcfce7', '#166534', d + ' gün'])); };
        var h = fmHead('🔧 Bakım hatırlatma', false) + '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px">' + fmMini('Geciken', r.overdue, '#fef2f2') + fmMini('Bugün', r.today, '#fffbeb') + fmMini('7 gün içinde', r.week, '#ecfeff') + fmMini('Toplam kayıt', r.items.length) + '</div>' +
          '<button id="mt-new" style="' + FB + ';margin-top:10px">＋ Yeni bakım kaydı</button><div style="margin:10px 0 4px">' + chip('all', 'Hepsi') + chip('due', 'Gelen/Geciken') + chip('week', 'Bu hafta') + '</div>' +
          (items.length ? items.map(function (x) { var p = pill(x); return '<div style="border:1px solid #e2e8f0;border-radius:12px;padding:10px;margin-top:8px"><span class="spx-pill" style="float:right;background:' + p[0] + ';color:' + p[1] + '">' + p[2] + '</span><b>' + esc(x.name) + '</b><div style="font-size:13px;color:#475569;margin-top:2px">' + esc(x.phone || '') + (x.address ? ' · ' + esc(x.address) : '') + '</div><div style="font-size:13px;color:#475569">' + esc(x.device || '') + ' · Son: ' + fmDt(x.last_date) + '</div><div style="font-size:13px">Sonraki bakım: <b>' + fmDt(x.next_date) + '</b></div>' + (x.note ? '<div style="font-size:12px;color:#64748b">' + esc(x.note) + '</div>' : '') +
            '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px"><button data-wa="' + x.id + '" style="border:0;border-radius:9px;background:#16a34a;color:#fff;font-weight:700;padding:7px 12px;cursor:pointer"' + (fmWaPhone(x.phone).length < 10 ? ' disabled style="opacity:.4"' : '') + '>WhatsApp mesajı</button><button data-dn="' + x.id + '" style="border:1px solid #0E9AA7;background:#fff;color:#0E9AA7;border-radius:9px;font-weight:700;padding:7px 12px;cursor:pointer">Bakım yapıldı</button><button data-ed="' + x.id + '" style="border:1px solid #cbd5e1;background:#fff;border-radius:9px;padding:7px 12px;cursor:pointer">Düzenle</button><button data-dl="' + x.id + '" style="border:1px solid #fecaca;background:#fff;color:#b91c1c;border-radius:9px;padding:7px 12px;cursor:pointer">Sil</button></div></div>'; }).join('') : '<div style="color:#64748b;padding:18px 0;text-align:center">Kayıt yok. “Yeni bakım kaydı” ile müşterinizi ekleyin.</div>') +
          '<details style="margin-top:14px"><summary style="cursor:pointer;font-weight:700;font-size:13px">WhatsApp mesaj metni</summary><textarea id="mt-msg" rows="4" style="margin-top:6px">' + esc(mtMsg()) + '</textarea><small style="color:#64748b;display:block">Kısa kodlar: {ad} {firma} {telefon} {tarih}</small><button id="mt-ms" style="border:1px solid #cbd5e1;background:#fff;border-radius:9px;padding:7px 12px;cursor:pointer;margin-top:6px">Metni kaydet</button></details>';
        m.firstChild.innerHTML = h; fmBind(m);
        document.getElementById('mt-new').onclick = function () { form(); };
        Array.prototype.forEach.call(m.querySelectorAll('[data-f]'), function (b) { b.onclick = function () { flt = b.getAttribute('data-f'); list(); }; });
        var by = function (id) { return data.items.filter(function (x) { return x.id === id; })[0]; };
        Array.prototype.forEach.call(m.querySelectorAll('[data-wa]'), function (b) { b.onclick = function () { var x = by(b.getAttribute('data-wa')); window.open('https://wa.me/' + fmWaPhone(x.phone) + '?text=' + encodeURIComponent(mtText(x)), '_blank'); }; });
        Array.prototype.forEach.call(m.querySelectorAll('[data-dn]'), function (b) { b.onclick = function () { if (!confirm('Bakım yapıldı olarak işaretlensin mi? Sonraki bakım tarihi otomatik ileri alınır.')) return; pcall('POST', '/firm/maint/' + b.getAttribute('data-dn') + '/done').then(function (r) { toast('Sonraki bakım: ' + fmDt(r.next_date)); MT_LAST = 0; list(); }).catch(function (e) { toast(e.message); }); }; });
        Array.prototype.forEach.call(m.querySelectorAll('[data-ed]'), function (b) { b.onclick = function () { form(by(b.getAttribute('data-ed'))); }; });
        Array.prototype.forEach.call(m.querySelectorAll('[data-dl]'), function (b) { b.onclick = function () { if (!confirm('Kayıt silinsin mi?')) return; pcall('DELETE', '/firm/maint/' + b.getAttribute('data-dl')).then(function () { MT_LAST = 0; list(); }).catch(function (e) { toast(e.message); }); }; });
        document.getElementById('mt-ms').onclick = function () { try { localStorage.setItem('spx_mt_msg', document.getElementById('mt-msg').value || ''); toast('Mesaj metni kaydedildi'); } catch (e) { } };
      }).catch(function (e) { m.remove(); toast(e.message || 'Yüklenemedi'); });
    };
    list();
  }
  function firmViewCash() {
    var m = fmShell(true), mon = new Date().toISOString().slice(0, 7), kind = '';
    var load = function () {
      pcall('GET', '/firm/cash?month=' + mon).then(function (r) {
        var h = fmHead('💰 Kasa hareketleri', true) + '<label style="margin-top:4px">Ay<input id="kc-m" type="month" value="' + esc(r.month) + '"></label>' +
          '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">' + fmMini('Gelir (ay)', fmTL(r.month_income), '#ecfdf5') + fmMini('Gider (ay)', fmTL(r.month_expense), '#fef2f2') + fmMini('Kasa bakiyesi', fmTL(r.balance), '#ecfeff') + '</div>' +
          '<div style="display:flex;gap:8px;margin-top:10px"><button id="kc-g" style="flex:1;border:0;border-radius:12px;background:#16a34a;color:#fff;font-weight:700;padding:12px;cursor:pointer">＋ Gelir ekle</button><button id="kc-d" style="flex:1;border:0;border-radius:12px;background:#dc2626;color:#fff;font-weight:700;padding:12px;cursor:pointer">－ Gider ekle</button></div><div id="kc-f"></div>' +
          (r.items.length ? r.items.map(function (x) { var g = x.kind === 'gelir'; return '<div style="border:1px solid #e2e8f0;border-radius:12px;padding:10px;margin-top:8px"><div style="display:flex;justify-content:space-between;gap:8px"><b>' + esc(x.title) + '</b><b style="color:' + (g ? '#16a34a' : '#dc2626') + ';white-space:nowrap">' + (g ? '+' : '−') + fmTL(x.amount) + '</b></div><small style="color:#64748b">' + fmDt(x.date) + ' · ' + esc(x.method || '') + '</small> <button data-del="' + x.id + '" style="border:0;background:none;color:#b91c1c;text-decoration:underline;cursor:pointer;font-size:12px">sil</button></div>'; }).join('') : '<div style="color:#64748b;padding:18px 0;text-align:center">Bu ay hareket yok.</div>');
        m.firstChild.innerHTML = h; fmBind(m);
        document.getElementById('kc-m').onchange = function () { if (this.value) { mon = this.value; load(); } };
        var open = function (k) {
          kind = k; var f = document.getElementById('kc-f');
          f.innerHTML = '<div style="border:1px dashed #94a3b8;border-radius:12px;padding:10px;margin-top:10px"><b>' + (k === 'gelir' ? 'Yeni gelir' : 'Yeni gider') + '</b><label>Açıklama<input id="kc-t"></label><div style="display:flex;gap:8px"><label style="flex:1">Tutar (₺)<input id="kc-a" type="number" min="0" step="0.01" inputmode="decimal"></label><label style="flex:1">Ödeme<select id="kc-y"><option value="nakit">Nakit</option><option value="kart">Kart</option><option value="havale">Havale</option></select></label></div><label>Tarih<input id="kc-dt" type="date" value="' + new Date().toISOString().slice(0, 10) + '"></label><button id="kc-s" style="' + FB + '">Kaydet</button></div>';
          document.getElementById('kc-s').onclick = function () {
            var btn = this; btn.disabled = true;
            pcall('POST', '/firm/cash', { kind: kind, amount: parseFloat(document.getElementById('kc-a').value), title: fmV('kc-t'), method: document.getElementById('kc-y').value, date: document.getElementById('kc-dt').value }).then(function () { toast('Kaydedildi'); load(); }).catch(function (e) { btn.disabled = false; toast(e.message || 'Kaydedilemedi'); });
          };
        };
        document.getElementById('kc-g').onclick = function () { open('gelir'); }; document.getElementById('kc-d').onclick = function () { open('gider'); };
        Array.prototype.forEach.call(m.querySelectorAll('[data-del]'), function (b) { b.onclick = function () { if (!confirm('Hareket silinsin mi?')) return; pcall('DELETE', '/firm/cash/' + b.getAttribute('data-del')).then(load).catch(function (e) { toast(e.message); }); }; });
      }).catch(function (e) { m.remove(); toast(e.message || 'Yüklenemedi'); });
    };
    load();
  }
  function firmViewStock() {
    var m = fmShell(true), data = null;
    var form = function (s) {
      s = s || {};
      m.firstChild.innerHTML = fmHead(s.id ? 'Ürünü düzenle' : 'Yeni ürün', true) + '<label>Ürün adı *<input id="ks-n" value="' + esc(s.name || '') + '"></label>' +
        '<div style="display:flex;gap:8px"><label style="flex:1">' + (s.id ? 'Adet (hareketle değişir)' : 'Başlangıç adedi') + '<input id="ks-q" type="number" min="0" step="1" value="' + (s.qty != null ? s.qty : 0) + '"' + (s.id ? ' disabled' : '') + '></label><label style="flex:1">Birim fiyat (₺)<input id="ks-p" type="number" min="0" step="0.01" value="' + (s.unit_price || 0) + '"></label></div>' +
        '<div style="display:flex;gap:8px"><label style="flex:1">Kritik seviye (uyarı)<input id="ks-m" type="number" min="0" step="1" value="' + (s.min_qty || 0) + '"></label><label style="flex:1">Raf / yer<input id="ks-y" value="' + esc(s.place || '') + '"></label></div><button id="ks-s" style="' + FB + '">Kaydet</button>';
      fmBind(m); document.getElementById('fi-b').onclick = list;
      document.getElementById('ks-s').onclick = function () {
        var btn = this, b = { name: fmV('ks-n'), qty: parseFloat(document.getElementById('ks-q').value) || 0, unit_price: parseFloat(document.getElementById('ks-p').value) || 0, min_qty: parseFloat(document.getElementById('ks-m').value) || 0, place: fmV('ks-y') };
        if (!b.name) { toast('Ürün adı yazın'); return; }
        btn.disabled = true; pcall(s.id ? 'PUT' : 'POST', '/firm/stock' + (s.id ? '/' + s.id : ''), b).then(function () { toast('Kaydedildi'); list(); }).catch(function (e) { btn.disabled = false; toast(e.message || 'Kaydedilemedi'); });
      };
    };
    var list = function () {
      pcall('GET', '/firm/stock').then(function (r) {
        data = r;
        var h = fmHead('📦 Stok yönetimi', true) + '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px">' + fmMini('Ürün çeşidi', r.count, '#ecfeff') + fmMini('Azalan', r.low, '#fef2f2') + fmMini('Stok değeri', fmTL(r.value), '#f0fdf4') + '</div><button id="ks-new" style="' + FB + ';margin-top:10px">＋ Yeni ürün</button>' +
          (r.items.length ? r.items.map(function (x) { return '<div style="border:1px solid ' + (x.low ? '#fca5a5' : '#e2e8f0') + ';border-radius:12px;padding:10px;margin-top:8px"><div style="display:flex;justify-content:space-between;gap:8px"><b>' + esc(x.name) + '</b><b style="color:' + (x.low ? '#b91c1c' : '#0f172a') + '">' + x.qty + ' adet' + (x.low ? ' ⚠' : '') + '</b></div><small style="color:#64748b">' + fmTL(x.unit_price) + (x.place ? ' · ' + esc(x.place) : '') + (x.min_qty ? ' · kritik ' + x.min_qty : '') + '</small><div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px"><button data-in="' + x.id + '" style="border:1px solid #16a34a;color:#16a34a;background:#fff;border-radius:9px;font-weight:700;padding:6px 12px;cursor:pointer">＋ Giriş</button><button data-out="' + x.id + '" style="border:1px solid #dc2626;color:#dc2626;background:#fff;border-radius:9px;font-weight:700;padding:6px 12px;cursor:pointer">− Çıkış</button><button data-ed="' + x.id + '" style="border:1px solid #cbd5e1;background:#fff;border-radius:9px;padding:6px 12px;cursor:pointer">Düzenle</button><button data-dl="' + x.id + '" style="border:1px solid #fecaca;background:#fff;color:#b91c1c;border-radius:9px;padding:6px 12px;cursor:pointer">Sil</button></div></div>'; }).join('') : '<div style="color:#64748b;padding:18px 0;text-align:center">Henüz ürün yok.</div>');
        m.firstChild.innerHTML = h; fmBind(m);
        document.getElementById('ks-new').onclick = function () { form(); };
        var by = function (id) { return data.items.filter(function (x) { return x.id === id; })[0]; };
        var mv = function (id, k) { var v = prompt((k === 'giris' ? 'Kaç adet stoğa eklensin?' : 'Kaç adet stoktan çıksın?'), '1'); if (v == null) return; var q = parseFloat(String(v).replace(',', '.')); if (!(q > 0)) { toast('Geçerli bir adet yazın'); return; } pcall('POST', '/firm/stock/' + id + '/move', { kind: k, qty: q }).then(function (r) { toast('Stok: ' + r.qty + ' adet'); list(); }).catch(function (e) { toast(e.message || 'Yapılamadı'); }); };
        Array.prototype.forEach.call(m.querySelectorAll('[data-in]'), function (b) { b.onclick = function () { mv(b.getAttribute('data-in'), 'giris'); }; });
        Array.prototype.forEach.call(m.querySelectorAll('[data-out]'), function (b) { b.onclick = function () { mv(b.getAttribute('data-out'), 'cikis'); }; });
        Array.prototype.forEach.call(m.querySelectorAll('[data-ed]'), function (b) { b.onclick = function () { form(by(b.getAttribute('data-ed'))); }; });
        Array.prototype.forEach.call(m.querySelectorAll('[data-dl]'), function (b) { b.onclick = function () { if (!confirm('Ürün silinsin mi?')) return; pcall('DELETE', '/firm/stock/' + b.getAttribute('data-dl')).then(list).catch(function (e) { toast(e.message); }); }; });
      }).catch(function (e) { m.remove(); toast(e.message || 'Yüklenemedi'); });
    };
    list();
  }
  /* iş detayında (yalnız yönetici): işi bir kullanıcıya ata */
  var ASG = { users: null, busy: false };
  function firmAssign() {
    var mt = location.pathname.match(/^\/tech\/jobs\/([^\/]+)\/?$/), box = document.getElementById('spx-asg');
    if (!FIRM || FIRM.sub || !mt) { if (box) box.remove(); return; }
    if (box && box.getAttribute('data-j') === mt[1]) return;
    if (box) box.remove();
    var mn = document.querySelector('main'); if (!mn || ASG.busy) return;
    ASG.busy = true;
    Promise.all([ASG.users ? Promise.resolve(ASG.users) : pcall('GET', '/firm/users'), pcall('GET', '/jobs/' + mt[1])]).then(function (a) {
      ASG.users = a[0]; var j = a[1], us = (a[0].users || []).filter(function (u) { return u.active !== false; });
      if (!us.length || document.getElementById('spx-asg') || location.pathname.indexOf(mt[1]) < 0) return;
      var d = document.createElement('div'); d.id = 'spx-asg'; d.setAttribute('data-j', mt[1]);
      d.style.cssText = 'border:1px solid #cbd5e1;border-radius:12px;background:#f8fafc;padding:10px;margin:10px 0;font-size:13px';
      d.innerHTML = '<b>İşi ata</b><select style="width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:10px;padding:9px;margin-top:6px;font-size:15px;background:#fff"><option value="">Atanmamış (yalnız ben görürüm)</option>' + us.map(function (u) { return '<option value="' + esc(u.email) + '"' + (j.assigned_to_fu === u.email ? ' selected' : '') + '>' + esc(u.name || u.email) + '</option>'; }).join('') + '</select>';
      d.querySelector('select').onchange = function () { var s = this; pcall('PUT', '/firm/jobs/' + mt[1] + '/assign', { assignee: s.value }).then(function (r) { toast(r.assigned_to_name ? r.assigned_to_name + ' kullanıcısına atandı' : 'Atama kaldırıldı'); }).catch(function (e) { toast(e.message || 'Atanamadı'); }); };
      mn.insertBefore(d, mn.firstChild);
    }).catch(function () { }).then(function () { ASG.busy = false; });
  }
  setInterval(function () { try { if (FIRM) { firmAssign(); firmMaintPoll(); } } catch (e) { } }, 1500);
  /* bilgisayar (web) görünümü: solda tam menü */
  function firmSide() {
    var s = document.getElementById('spx-fside');
    if (!FIRM || !FFRESH || window.innerWidth < 1024) { if (s) s.remove(); document.body.classList.remove('spx-fside-on'); return; }
    document.body.classList.add('spx-fside-on');
    if (s) { if (!s.parentNode) document.body.appendChild(s); return; }
    s = document.createElement('div'); s.id = 'spx-fside'; s.className = 'notranslate';
    var go = function (f) { return function () { var op = document.getElementById('spx-fm'); if (op) op.remove(); var rv = document.getElementById('spx-rcv'); if (rv) rv.remove(); f(); }; };
    var it = [['📋', 'Görevler', function () { if (/^\/tech\/?$/.test(location.pathname)) { if (!firmTab('Aktif')) firmNavGo('tab-jobs', '/tech'); } else firmNavGo('tab-jobs', '/tech'); }], ['📝', 'Teklif', function () { firmNavGo('tab-quotes'); }, 'q'], ['＋', 'Yeni servis', firmNewJob], ['✔', 'Tamamlanan', function () { firmGo('Tamamlanan'); }], ['🔧', 'Bakım hatırlatma', firmViewMaint, 'b'], ['💰', 'Kasa hareketleri', firmViewCash, 'o'], ['📦', 'Stok yönetimi', firmViewStock, 'o'], ['📈', 'Ciro raporu', firmViewReport], ['👥', 'Kullanıcılar', firmViewUsers], ['🏢', 'Firma bilgileri', firmViewInfo], ['📄', 'PDF alt metni', firmViewPdf], ['🔑', 'Şifre değiştir', firmViewPass], ['↩', 'Çıkış', function () { try { localStorage.removeItem('token'); localStorage.removeItem('spx_firm'); } catch (e) { } location.href = '/login'; }]];
    var h = document.createElement('div'); h.className = 'spx-fs-t'; h.textContent = (FIRM.name || 'Firma'); s.appendChild(h);
    it.forEach(function (d) {
      if (d[3] === 'q' && !document.querySelector('nav a[data-testid=tab-quotes]')) return;
      if (d[3] === 'o' && FIRM.sub) return;
      var b = document.createElement('button'); b.type = 'button'; b.onclick = go(d[2]);
      b.innerHTML = '<span>' + d[0] + '</span><span style="flex:1;text-align:left">' + d[1] + '</span>' + (d[3] === 'b' ? '<i id="spx-mtb2" style="display:none"></i>' : '');
      s.appendChild(b);
    });
    document.body.appendChild(s); firmBadge();
  }
  setInterval(function () { try { firmSide(); } catch (e) { } }, 700);
  (function () {
    var st = document.createElement('style');
    st.textContent = '#spx-fside{display:none}@media(min-width:1024px){body.spx-fside-on #spx-fside{display:flex;flex-direction:column;position:fixed;left:0;top:0;bottom:0;width:230px;z-index:9994;background:#0f172a;padding:14px 10px;overflow:auto}body.spx-fside-on{padding-left:230px!important}body.spx-fside-on nav.fixed.bottom-0{display:none!important}body.spx-fside-on header{padding-left:0}#spx-fside .spx-fs-t{color:#fff;font-weight:800;font-size:16px;padding:6px 10px 14px;word-break:break-word}#spx-fside button{display:flex;align-items:center;gap:10px;width:100%;border:0;background:none;color:#cbd5e1;font-size:14px;font-weight:600;padding:10px;border-radius:9px;cursor:pointer;margin-bottom:2px;font-family:inherit}#spx-fside button:hover{background:#1e293b;color:#fff}#spx-fside button span:first-child{width:22px;text-align:center}body.spx-fside-on #spx-fm{left:230px}body.spx-fside-on #spx-ffab{right:24px}}' +
      '#spx-mtb,#spx-mtb2{background:#dc2626;color:#fff;border-radius:99px;font-size:10px;font-weight:800;font-style:normal;padding:1px 6px;line-height:14px}#spx-mtb{position:absolute;top:2px;left:calc(50% + 6px)}#spx-fbar button{position:relative}';
    document.head.appendChild(st);
  })();
  function firmNewJob() {
    if (document.getElementById('spx-fm')) return;
    var m = document.createElement('div'); m.id = 'spx-fm';
    m.innerHTML = '<div><div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:18px">Manuel servis ekle</b><button id="fm-x" style="border:0;background:none;font-size:26px;cursor:pointer">×</button></div>' +
      '<label>Müşteri adı soyadı *<input id="fm-n" autocomplete="off"></label><label>Telefon *<input id="fm-p" type="tel" placeholder="05xx xxx xx xx"></label>' +
      '<label>Adres<input id="fm-a"></label><div style="display:flex;gap:8px"><label style="flex:1">İl<input id="fm-c"></label><label style="flex:1">İlçe<input id="fm-d"></label></div>' +
      '<label>Cihaz türü<select id="fm-t"><option>Kombi</option><option>Klima</option><option>Şofben</option><option>Buzdolabı</option><option>Çamaşır makinesi</option><option>Bulaşık makinesi</option><option>Diğer</option></select></label>' +
      '<label>Marka<select id="fm-b"><option value="">Marka seçin</option></select></label><label>Model<input id="fm-m"></label>' +
      '<label>Arıza / yapılacak iş *<textarea id="fm-f" rows="3"></textarea></label>' +
      '<button id="fm-go" style="margin-top:14px;width:100%;border:0;border-radius:12px;background:#0E9AA7;color:#fff;font-weight:700;font-size:16px;padding:13px">Servisi kaydet</button></div>';
    document.body.appendChild(m);
    var hd = document.querySelector('header'); if (hd && window.innerWidth < 1024 && document.body.classList.contains('spx-fbar-on')) m.style.top = Math.max(0, Math.round(hd.getBoundingClientRect().bottom)) + 'px';   /* üst menü ve alt çubuk görünür */
    var close = function () { m.remove(); }; m.onclick = function (e) { if (e.target === m) close(); }; document.getElementById('fm-x').onclick = close;
    pcall('GET', '/brands').then(function (bs) { var s = document.getElementById('fm-b'); if (!s || !Array.isArray(bs)) return; bs.forEach(function (b) { var o = document.createElement('option'); o.value = b.id; o.textContent = b.name; s.appendChild(o); }); }).catch(function () { });
    var V = function (id) { return (document.getElementById(id).value || '').trim(); };
    document.getElementById('fm-go').onclick = function () {
      var btn = this, n = V('fm-n'), ph = V('fm-p'), f = V('fm-f');
      if (!n || !ph || !f) { toast('Müşteri adı, telefon ve arıza gerekli'); return; }
      btn.disabled = true; btn.textContent = 'Kaydediliyor…';
      var cust, dev = null;
      pcall('POST', '/customers', { name: n, phone: ph, address: V('fm-a'), city: V('fm-c'), district: V('fm-d') }).then(function (c) {
        cust = c; var br = V('fm-b');
        if (br) return pcall('POST', '/devices', { customer_id: c.id, brand_id: br, type: (V('fm-t') || 'cihaz').toLowerCase(), model: V('fm-m') }).then(function (d) { dev = d; });
      }).then(function () {
        return pcall('POST', '/jobs', { customer_id: cust.id, device_id: dev ? dev.id : '', fault_description: (V('fm-t') && !dev ? V('fm-t') + (V('fm-m') ? ' ' + V('fm-m') : '') + ' — ' : '') + f });
      }).then(function () { toast('Servis kaydedildi'); setTimeout(function () { location.href = '/tech'; location.reload(); }, 600); })
        .catch(function (e) { btn.disabled = false; btn.textContent = 'Servisi kaydet'; toast(e.message || 'Kaydedilemedi'); });
    };
  }
  setInterval(firmMode, 300);

  /* --- aç/kapat + ayarlar --- */
  function drawMod() {
    Promise.all([call('GET', '/admin/modules'), call('GET', '/site/features')]).then(function (a) {
      MOD = a[0]; FEAT = a[1]; var h = '';
      h += '<div class="spx-card"><b>Site bölümleri</b><small style="display:block;color:#64748b;margin-bottom:6px">Kapatılan bölüm sitede pasif olur (menüden ve sayfadan kalkar).</small>' +
        [['f_shop', 'Mağaza', 'Ürünler, sepet ve sipariş', FEAT.shop_enabled], ['f_acc', 'Müşteri girişi / Üyelik', 'Üye ol, giriş, hesabım', FEAT.customer_portal_enabled], ['f_qr', 'Hızlı servis talebi', '“Talebi Gönder” formu', FEAT.quick_request && FEAT.quick_request.enabled], ['f_lang', 'Dil seçenekleri', '', FEAT.language_enabled]].map(function (x) { return '<div class="spx-row"><div class="t"><b>' + x[1] + '</b><small>' + x[2] + '</small></div>' + sw(x[0], x[3]) + '</div>'; }).join('') + '</div>';
      var groups = {}; MOD.modules.forEach(function (m) { (groups[m.group] = groups[m.group] || []).push(m); });
      Object.keys(groups).forEach(function (g) {
        h += '<div class="spx-card"><b>' + esc(g) + '</b>';
        groups[g].forEach(function (m) {
          var c = (MOD.config || {})[m.id] || {};
          h += '<div class="spx-row" style="align-items:flex-start"><div class="t"><b>' + esc(m.label) + '</b><small>' + esc(m.desc) + '</small>';
          if (m.fields.length) h += '<div class="spx-g" style="margin-top:8px">' + m.fields.map(function (f) { var v = c[f.key] == null ? '' : c[f.key]; return '<label>' + esc(f.label) + (f.key === 'rules' ? '<textarea rows="3" data-c="' + m.id + '.' + f.key + '" placeholder="[{&quot;find&quot;:&quot;kombi servisi&quot;,&quot;url&quot;:&quot;/kombi-servisi/&quot;}]">' + esc(v) + '</textarea>' : '<input data-c="' + m.id + '.' + f.key + '" type="' + (f.secret ? 'password' : 'text') + '" value="' + esc(v) + '">') + '</label>'; }).join('') + '</div>';
          if (m.id === 'iyzico') h += '<div style="margin-top:8px"><button class="spx-b" data-test="iyz">Bağlantıyı test et</button></div>';
          if (m.id === 'merchant') h += '<div style="margin-top:8px"><small>Merchant Center besleme adresi:</small> <input readonly style="width:100%" value="' + esc(MOD.urls.merchant_feed) + '"></div>';
          if (m.id === 'merchant_api') h += '<div style="margin-top:8px"><button class="spx-b" data-test="mapi">Ürünleri Merchant Center\'a gönder</button></div>';
          h += '</div>' + sw('m_' + m.id, m.enabled) + '</div>';
        });
        h += '</div>';
      });
      h += '<div style="position:sticky;bottom:0;padding:8px 0"><button class="spx-b p" id="spx-save">Kaydet</button> <button class="spx-b" id="spx-imp">Site ürünlerini panele aktar</button> <small style="color:#64748b">Kaydedilen değişiklik sitede ~30 sn içinde görünür.</small></div>';
      body().innerHTML = h;
      $('#spx-save').onclick = saveMod; $('#spx-imp').onclick = function () { call('POST', '/shop/import-site-catalog', {}).then(function (r) { toast((r.added || 0) + ' ürün aktarıldı' + (r.added ? '' : ' (zaten aktarılmış)')); }).catch(fail); };
      body().addEventListener('click', function (e) {
        var bt = e.target.closest && e.target.closest('[data-hd]'); if (!bt) return;
        bt.disabled = true; bt.textContent = '…';
        call('GET', '/admin/brand-hub/' + bt.getAttribute('data-hd') + '/diag').then(function (d) {
          var t = 'Site: ' + d.site + '\nÜrün adresi deseni: ' + (d.link_regex || '(otomatik)') + '\n';
          (d.steps || []).forEach(function (st) {
            t += '\n' + st.url + '\n  ' + (st.error ? 'HATA: ' + st.error : 'HTTP ' + st.http + ' · ' + st.bytes + ' bayt · sayfadaki bağlantı: ' + st.links_total + ' · ürün adresi: ' + st.product_links + (st.robots_ok === false ? ' · robots.txt ENGELLİYOR' : '') + (st.title ? '\n  başlık: ' + st.title : '') + (st.sample && st.sample.length ? '\n  örnek: ' + st.sample[0] : '') + (st.body_start ? '\n  yanıt: ' + st.body_start.replace(/\s+/g, ' ') : '')); });
          alert(t);
        }).catch(fail).then(function () { bt.disabled = false; bt.textContent = 'Tanı'; });
      });
      body().onclick = function (e) { var b = e.target.closest('[data-test]'); if (!b) return; var t = b.getAttribute('data-test'); (t === 'iyz' ? call('POST', '/admin/payments/iyzico/test', {}) : call('POST', '/admin/merchant-api/push', {})).then(function (r) { toast(r.message || (r.ok ? 'Başarılı' : JSON.stringify(r).slice(0, 120))); }).catch(fail); };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  function saveMod() {
    var flags = {}, conf = {};
    MOD.modules.forEach(function (m) { flags[m.id] = $('#m_' + m.id).checked; });
    Array.prototype.forEach.call(body().querySelectorAll('[data-c]'), function (e) { var p = e.getAttribute('data-c').split('.'); (conf[p[0]] = conf[p[0]] || {})[p[1]] = e.value; });
    var qr = Object.assign({}, FEAT.quick_request, { enabled: $('#f_qr').checked });
    Promise.all([
      call('PUT', '/site/features', { shop_enabled: $('#f_shop').checked, customer_portal_enabled: $('#f_acc').checked, language_enabled: $('#f_lang').checked, quick_request: qr }),
      call('PUT', '/admin/modules', { flags: flags, config: conf })
    ]).then(function () { toast('Kaydedildi — site 30 sn içinde güncellenir'); drawMod(); }).catch(fail);
  }
  /* --- SEO / 301 / 404 / anahtar kelime --- */
  function drawSeo() {
    Promise.all([call('GET', '/admin/seo'), call('GET', '/admin/redirects'), call('GET', '/admin/404')]).then(function (a) {
      var h = '<div class="spx-card"><b>Toplu SEO kuralı</b><small style="display:block;color:#64748b">Adresi bu ile başlayan tüm sayfalara başlık/açıklama uygular. (Modüllerden “Toplu SEO” açık olmalı.)</small><div class="spx-g" style="margin:8px 0"><label>Adres öneki<input id="s_p" placeholder="/magaza"></label><label>Başlık<input id="s_t"></label><label>Açıklama<input id="s_d"></label><label>Robots<input id="s_r" placeholder="noindex,follow"></label><label>Canonical<input id="s_c"></label></div><button class="spx-b p" id="s_add">Kural ekle</button><table style="margin-top:8px"><tr><th>Önek</th><th>Başlık</th><th>Açıklama</th><th></th></tr>' + a[0].map(function (r) { return '<tr><td>' + esc(r.prefix) + '</td><td>' + esc(r.title) + '</td><td>' + esc(r.description) + '</td><td><button class="spx-b d" data-del="seo/' + r.id + '">Sil</button></td></tr>'; }).join('') + '</table></div>';
      h += '<div class="spx-card"><b>301 / 302 yönlendirme</b><div class="spx-g" style="margin:8px 0"><label>Eski adres<input id="r_s" placeholder="/eski-sayfa"></label><label>Yeni adres<input id="r_t" placeholder="/yeni-sayfa"></label><label>Kod<select id="r_c"><option>301</option><option>302</option></select></label></div><button class="spx-b p" id="r_add">Yönlendirme ekle</button> <button class="spx-b" id="r_ht">.htaccess çıktısı</button><table style="margin-top:8px"><tr><th>Eski</th><th>Yeni</th><th>Kod</th><th></th></tr>' + a[1].map(function (r) { return '<tr><td>' + esc(r.source) + '</td><td>' + esc(r.target) + '</td><td>' + r.code + '</td><td><button class="spx-b d" data-del="redirects/' + r.id + '">Sil</button></td></tr>'; }).join('') + '</table><pre id="r_out" style="white-space:pre-wrap"></pre></div>';
      h += '<div class="spx-card"><b>404 kayıtları</b><small style="display:block;color:#64748b">Ziyaretçilerin bulamadığı adresler. (Modüllerden “404 yönetimi” açık olmalı.)</small><table><tr><th>Adres</th><th>Sayı</th><th>Son</th><th></th></tr>' + a[2].map(function (r) { return '<tr><td>' + esc(r.path) + '</td><td>' + (r.count || r.hits || 1) + '</td><td>' + esc(String(r.last_seen || r.updated_at || '').slice(0, 16).replace('T', ' ')) + '</td><td><button class="spx-b" data-r404="' + esc(r.path) + '">301 yap</button> <button class="spx-b d" data-del="404/' + r.id + '">Sil</button></td></tr>'; }).join('') + '</table></div>';
      h += '<div class="spx-card"><b>Google anahtar kelime önerisi</b><div style="margin:8px 0"><input id="k_q" placeholder="kombi servisi ankara" style="width:260px"> <button class="spx-b p" id="k_go">Öner</button></div><div id="k_out"></div></div>';
      body().innerHTML = h;
      var reload = function (m) { return function () { toast(m || 'Tamam'); drawSeo(); }; };
      $('#s_add').onclick = function () { call('POST', '/admin/seo', { prefix: $('#s_p').value.trim(), title: $('#s_t').value, description: $('#s_d').value, robots: $('#s_r').value, canonical: $('#s_c').value }).then(reload('Kural eklendi')).catch(fail); };
      $('#r_add').onclick = function () { call('POST', '/admin/redirects', { source: $('#r_s').value.trim(), target: $('#r_t').value.trim(), code: +$('#r_c').value }).then(reload('Yönlendirme eklendi')).catch(fail); };
      $('#r_ht').onclick = function () { call('GET', '/admin/redirects-htaccess').then(function (r) { $('#r_out').textContent = r.text; }).catch(fail); };
      $('#k_go').onclick = function () { call('GET', '/admin/keywords?q=' + encodeURIComponent($('#k_q').value)).then(function (r) { var l = r.suggestions || r.items || r; $('#k_out').innerHTML = (Array.isArray(l) ? l : []).map(function (x) { return '<span class="spx-pill" style="margin:2px">' + esc(typeof x === 'string' ? x : x.keyword || x.text) + '</span>'; }).join(' ') || 'Sonuç yok'; }).catch(fail); };
      body().onclick = function (e) {
        var d = e.target.closest('[data-del]'); if (d) { call('DELETE', '/admin/' + d.getAttribute('data-del')).then(reload('Silindi')).catch(fail); return; }
        var r4 = e.target.closest('[data-r404]'); if (r4) { var to = prompt('Bu adres nereye yönlensin?', '/'); if (to) call('POST', '/admin/redirects', { source: r4.getAttribute('data-r404'), target: to, code: 301 }).then(reload('Yönlendirme eklendi')).catch(fail); }
      };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  /* --- panelden sipariş --- */
  function drawNew() {
    call('GET', '/shop/products').then(function (ps) {
      ps = Array.isArray(ps) ? ps : (ps.items || []);
      body().innerHTML = '<div class="spx-card"><b>Telefon / WhatsApp siparişi gir</b><div class="spx-g" style="margin:8px 0"><label>Ad Soyad<input id="o_n"></label><label>Telefon<input id="o_p"></label><label>E-posta<input id="o_e"></label><label>İl<input id="o_c"></label><label>İlçe<input id="o_d"></label><label>Adres<input id="o_a"></label></div>' +
        '<table id="o_t"><tr><th>Ürün</th><th>Adet</th></tr></table><button class="spx-b" id="o_more">+ Ürün satırı</button><div style="margin-top:10px"><button class="spx-b p" id="o_go">Siparişi oluştur</button></div><div id="o_res"></div></div>';
      var opts = ps.map(function (p) { return '<option value="' + esc(p.id) + '">' + esc(p.name) + ' — ' + (p.price || 0) + ' ₺</option>'; }).join('');
      var addRow = function () { var tr = document.createElement('tr'); tr.innerHTML = '<td><select class="o_pr">' + opts + '</select></td><td><input class="o_q" type="number" min="1" value="1" style="width:70px"></td>'; $('#o_t').appendChild(tr); };
      if (!ps.length) { $('#o_res').innerHTML = '<small>Mağazada ürün yok. “Aç/Kapat & Ayarlar” sekmesinden “Site ürünlerini panele aktar” düğmesine basın.</small>'; } else addRow();
      $('#o_more').onclick = addRow;
      $('#o_go').onclick = function () {
        var items = Array.prototype.map.call(document.querySelectorAll('#o_t tr'), function (tr) { var s = tr.querySelector('.o_pr'); return s ? { product_id: s.value, qty: +tr.querySelector('.o_q').value || 1 } : null; }).filter(Boolean);
        call('POST', '/shop/orders-create', { name: $('#o_n').value, phone: $('#o_p').value, email: $('#o_e').value, city: $('#o_c').value, district: $('#o_d').value, address: $('#o_a').value, items: items }).then(function (r) { $('#o_res').innerHTML = '<p><b>Sipariş oluşturuldu: ' + esc(r.order_no) + '</b> — ' + (r.total || '') + ' ₺ (Mağaza → Siparişler’de görünür)</p>'; toast('Sipariş ' + r.order_no); }).catch(fail);
      };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  /* --- pazaryerleri --- */
  function drawMkt() {
    call('GET', '/admin/market/orders').then(function (os) {
      os = Array.isArray(os) ? os : (os.items || []);
      var ids = [['trendyol', 'Trendyol'], ['hepsiburada', 'Hepsiburada'], ['n11', 'N11']];
      body().innerHTML = '<div class="spx-card"><b>Pazaryeri işlemleri</b><small style="display:block;color:#64748b;margin-bottom:8px">Önce “Aç/Kapat & Ayarlar” sekmesinden ilgili pazaryerinin anahtarlarını girip açın.</small>' + ids.map(function (m) { return '<div class="spx-row"><div class="t"><b>' + m[1] + '</b></div><button class="spx-b" data-m="' + m[0] + ':test">Bağlantı testi</button><button class="spx-b" data-m="' + m[0] + ':pull-orders">Siparişleri çek</button><button class="spx-b" data-m="' + m[0] + ':push-stock">Stok/fiyat gönder</button></div>'; }).join('') + '</div>' +
        '<div class="spx-card"><b>Çekilen siparişler</b><table><tr><th>Pazaryeri</th><th>No</th><th>Müşteri</th><th>Tutar</th><th>Durum</th></tr>' + os.map(function (o) { return '<tr><td>' + esc(o.market) + '</td><td>' + esc(o.order_no || o.external_id) + '</td><td>' + esc(o.customer || (o.customer && o.customer.name) || '') + '</td><td>' + esc(o.total) + '</td><td>' + esc(o.status) + '</td></tr>'; }).join('') + '</table></div>';
      body().onclick = function (e) { var b = e.target.closest('[data-m]'); if (!b) return; var p = b.getAttribute('data-m').split(':'); b.disabled = true; call('POST', '/admin/market/' + p[0] + '/' + p[1], {}).then(function (r) { toast(r.message || ('Tamam' + (r.count != null ? ': ' + r.count : ''))); b.disabled = false; if (p[1] === 'pull-orders') drawMkt(); }).catch(function (e) { b.disabled = false; fail(e); }); };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }

  /* --- kullanıcılar & yetkiler --- */
  var PRESETS = [['Muhasebe', ['accounting', 'reports']], ['Sipariş & Mağaza', ['shop', 'coupons', 'customers']], ['Servis operasyon', ['jobs', 'appointments', 'quotes', 'warranty', 'customers', 'technicians', 'parts']], ['Site editörü', ['studio', 'seo', 'site_features']], ['Mesajlar', ['messages', 'reviews', 'dealers']]];
  function permGrid(mods, sel, pre) {
    var groups = {}, order = []; mods.forEach(function (m) { if (!groups[m.group]) { groups[m.group] = []; order.push(m.group); } groups[m.group].push(m); });
    return '<div style="margin:6px 0">' + PRESETS.map(function (p, i) { return '<button type="button" class="spx-b" data-preset="' + pre + ':' + i + '" style="margin:0 6px 6px 0">' + esc(p[0]) + '</button>'; }).join('') + '<button type="button" class="spx-b" data-all="' + pre + ':1" style="margin:0 6px 6px 0">Tümünü seç</button><button type="button" class="spx-b" data-all="' + pre + ':0" style="margin:0 6px 6px 0">Temizle</button></div>' +
      '<div class="spx-g" id="' + pre + '-grid" style="grid-template-columns:repeat(auto-fit,minmax(260px,1fr));align-items:start">' + order.map(function (g) { return '<div class="spx-card" style="margin:0"><b>' + esc(g) + '</b>' + groups[g].map(function (m) { return '<label style="display:flex;gap:8px;align-items:flex-start;margin:7px 0;font-size:13px;color:inherit"><input type="checkbox" data-pm="' + m.key + '"' + (sel.indexOf(m.key) >= 0 ? ' checked' : '') + ' style="width:auto;margin-top:2px"> <span>' + esc(m.label) + '</span></label>'; }).join('') + '</div>'; }).join('') + '</div>';
  }
  function gridVals(pre) { return Array.prototype.map.call(document.querySelectorAll('#' + pre + '-grid [data-pm]:checked'), function (e) { return e.getAttribute('data-pm'); }); }
  function describe(u, mods) {
    var r = u.admin_role || 'owner'; if (r === 'owner') return 'Sahip — her şeyi görür'; if (r === 'manager') return 'Müdür — güvenlik/yedek/kullanıcılar hariç her şey'; if (r !== 'custom') return ({ accounting: 'Muhasebe (eski rol)', operations: 'Operasyon (eski rol)', site_editor: 'Site editörü (eski rol)' })[r] || r;
    var names = (u.perms || []).map(function (k) { var m = mods.filter(function (x) { return x.key === k; })[0]; return m ? m.label.split(' · ')[0].split(' (')[0] : k; });
    return (names.length ? names.join(', ') : 'Hiçbir bölüm seçilmemiş') + (u.perms_ro ? ' — salt okunur' : '');
  }
  function drawUsers() {
    Promise.all([call('GET', '/admin-users'), call('GET', '/governance/perm-modules')]).then(function (a) {
      var list = a[0], mods = a[1], me = {}; try { me = JSON.parse(LS.get('user', '{}')) || {}; } catch (e) { }
      var h = '<div class="spx-card"><b>Yeni kullanıcı ekle</b><small style="display:block;color:#64748b;margin-bottom:8px">Kullanıcı yalnızca aşağıda işaretlediğiniz bölümleri görür ve kullanabilir. İşaretlenmeyen bölümler menüde görünmez, adresi yazsa bile açılmaz.</small>' +
        '<div class="spx-g"><label>Ad Soyad<input id="nu_n"></label><label>E-posta<input id="nu_e" type="email"></label><label>Şifre (en az 6)<input id="nu_p" type="password"></label><label>Telefon<input id="nu_t"></label></div>' +
        '<div style="margin-top:10px"><b>Hangi bölümleri görebilsin?</b></div>' + permGrid(mods, [], 'nu') +
        '<label style="display:flex;gap:8px;align-items:center;margin:10px 0;color:inherit"><input type="checkbox" id="nu_ro" style="width:auto"> Sadece görüntüleyebilsin (kayıt ekleyemesin / değiştiremesin)</label><button class="spx-b p" id="nu_go">Kullanıcıyı oluştur</button></div>';
      h += '<div class="spx-card"><b>Mevcut kullanıcılar</b><table style="margin-top:8px"><tr><th>Kullanıcı</th><th>Erişim</th><th>Aktif</th><th></th></tr>' + list.map(function (u) {
        return '<tr><td><b>' + esc(u.name) + '</b>' + (u.id === me.id ? ' <span class="spx-pill">siz</span>' : '') + '<br><small style="color:#64748b">' + esc(u.email) + '</small></td><td>' + esc(describe(u, mods)) + '</td><td>' + sw('ua_' + u.id, u.is_active !== false) + '</td><td style="white-space:nowrap"><button class="spx-b" data-ue="' + u.id + '">Yetkileri düzenle</button> <button class="spx-b" data-up="' + u.id + '">Şifre</button>' + (u.id === me.id ? '' : ' <button class="spx-b d" data-ud="' + u.id + '">Sil</button>') + '</td></tr><tr id="ued_' + u.id + '" style="display:none"><td colspan="4"></td></tr>';
      }).join('') + '</table></div>';
      body().innerHTML = h;
      var byId = {}; list.forEach(function (u) { byId[u.id] = u; });
      $('#nu_go').onclick = function () {
        var perms = gridVals('nu'); if (!$('#nu_n').value.trim() || !$('#nu_e').value.trim() || $('#nu_p').value.length < 6) { toast('Ad, e-posta ve en az 6 karakterli şifre gerekli'); return; } if (!perms.length) { toast('En az bir bölüm seçin'); return; }
        call('POST', '/admin-users', { name: $('#nu_n').value.trim(), email: $('#nu_e').value.trim(), password: $('#nu_p').value, phone: $('#nu_t').value, admin_role: 'manager' }).then(function (u) { return call('PUT', '/governance/admins/' + u.id + '/perms', { perms: perms, ro: $('#nu_ro').checked }); }).then(function () { toast('Kullanıcı oluşturuldu'); drawUsers(); }).catch(fail);
      };
      body().onclick = function (e) {
        var t = e.target;
        var pr = t.closest('[data-preset]'); if (pr) { var x = pr.getAttribute('data-preset').split(':'), set = PRESETS[+x[1]][1]; Array.prototype.forEach.call(document.querySelectorAll('#' + x[0] + '-grid [data-pm]'), function (c) { if (set.indexOf(c.getAttribute('data-pm')) >= 0) c.checked = true; }); return; }
        var al = t.closest('[data-all]'); if (al) { var y = al.getAttribute('data-all').split(':'); Array.prototype.forEach.call(document.querySelectorAll('#' + y[0] + '-grid [data-pm]'), function (c) { c.checked = y[1] === '1'; }); return; }
        var ed = t.closest('[data-ue]'); if (ed) { var id = ed.getAttribute('data-ue'), u = byId[id], row = $('#ued_' + id); if (row.style.display !== 'none') { row.style.display = 'none'; return; } row.style.display = 'table-row';
          var mode = (u.admin_role === 'owner' || !u.admin_role) ? 'owner' : u.admin_role === 'manager' ? 'manager' : 'custom';
          row.firstChild.innerHTML = '<div style="padding:8px 0"><label style="color:inherit">Erişim türü <select id="em_' + id + '"><option value="custom">Tek tek seçtiklerim</option><option value="manager">Müdür (her şey, güvenlik/yedek/kullanıcılar hariç)</option><option value="owner">Sahip (her şey)</option></select></label><div id="eg_' + id + '">' + permGrid(mods, u.perms || [], 'e' + id) + '<label style="display:flex;gap:8px;align-items:center;margin:10px 0;color:inherit"><input type="checkbox" id="er_' + id + '" style="width:auto"' + (u.perms_ro ? ' checked' : '') + '> Sadece görüntüleyebilsin</label></div><button class="spx-b p" data-us="' + id + '">Kaydet</button></div>';
          var sel = $('#em_' + id); sel.value = mode; sel.onchange = function () { $('#eg_' + id).style.display = sel.value === 'custom' ? 'block' : 'none'; }; sel.onchange(); return; }
        var sv = t.closest('[data-us]'); if (sv) { var id2 = sv.getAttribute('data-us'), md = $('#em_' + id2).value; var p = md === 'custom' ? call('PUT', '/governance/admins/' + id2 + '/perms', { perms: gridVals('e' + id2), ro: $('#er_' + id2).checked }) : call('PUT', '/governance/admins/' + id2 + '/role', { role: md }); if (md === 'custom' && !gridVals('e' + id2).length) { toast('En az bir bölüm seçin'); return; } p.then(function () { toast('Yetkiler kaydedildi (kullanıcı yeniden giriş yapar)'); drawUsers(); }).catch(fail); return; }
        var up = t.closest('[data-up]'); if (up) { var pw = prompt('Yeni şifre (en az 6 karakter):'); if (pw) call('PUT', '/admin-users/' + up.getAttribute('data-up'), { password: pw }).then(function () { toast('Şifre değişti'); }).catch(fail); return; }
        var ud = t.closest('[data-ud]'); if (ud) { var u3 = byId[ud.getAttribute('data-ud')]; if (confirm(u3.name + ' silinsin mi? Bir daha giriş yapamaz.')) call('DELETE', '/admin-users/' + u3.id).then(function () { toast('Silindi'); drawUsers(); }).catch(fail); return; }
      };
      body().onchange = function (e) { var c = e.target; if (c.id && c.id.indexOf('ua_') === 0) { call('PUT', '/admin-users/' + c.id.slice(3), { is_active: c.checked }).then(function () { toast(c.checked ? 'Aktif' : 'Pasif yapıldı'); }).catch(function (er) { c.checked = !c.checked; fail(er); }); } };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }

  /* --- Google Search Console --- */
  function fdt(s) { return s ? esc(String(s).replace('T', ' ').slice(0, 16)) : '—'; }
  function drawGsc() {
    call('GET', '/admin/gsc/status').then(function (st) {
      var h = '';
      var c = st.config, lr = st.last_result || {};
      /* 1. bağlantı */
      h += '<div class="spx-card"><b>1 · Google bağlantısı</b> ' + (st.connected ? '<span class="spx-pill" style="background:#dcfce7;color:#166534">Bağlı</span>' : '<span class="spx-pill" style="background:#fee2e2;color:#991b1b">Bağlı değil</span>') +
        (st.connected ? '<div style="margin:8px 0">Mülk: <b>' + esc(st.property || 'otomatik bulunacak') + '</b> <select id="g_prop" style="margin-left:6px"><option>Yükleniyor…</option></select> <button class="spx-b" id="g_dis">Bağlantıyı kes</button></div>' :
        '<div style="margin:8px 0;color:#64748b;font-size:13px">Google Cloud’da (console.cloud.google.com) “OAuth istemci kimliği → Web uygulaması” oluşturun, “Search Console API”yi etkinleştirin ve <b>Yetkili yönlendirme URI</b> olarak şunu ekleyin:<br><input readonly style="width:100%" value="' + esc(st.redirect_uri) + '" onclick="this.select()"></div>' +
        '<div class="spx-g"><label>İstemci kimliği<input id="g_cid" value="' + esc(st.client_id) + '"></label><label>İstemci gizli anahtarı<input id="g_cs" type="password" placeholder="' + (st.has_client ? '(kayıtlı — değiştirmek için yazın)' : '') + '"></label></div>' +
        '<div style="margin-top:8px"><button class="spx-b" id="g_save">Kaydet</button> <button class="spx-b p" id="g_conn">Google ile bağlan</button> <small style="color:#64748b">Açılan pencerede Search Console’da sahibi olduğunuz hesabı seçin.</small></div>') + '</div>';
      /* 2. otomasyon */
      h += '<div class="spx-card"><b>2 · Otomasyon</b><div class="spx-row"><div class="t"><b>Otomatik çalış</b><small>Sitemap’i Google’a gönderir, sayfaları denetler, arama verisini çeker. Panel açık olmasa da sunucuda çalışır.</small></div>' + sw('g_auto', c.auto) + '</div>' +
        '<div class="spx-g" style="margin:8px 0"><label>Kaç saatte bir<input id="g_int" type="number" min="6" max="168" value="' + c.interval_h + '"></label><label>Her seferde denetlenecek sayfa (0–200)<input id="g_ins" type="number" min="0" max="200" value="' + c.inspect_per_run + '"></label></div>' +
        '<label style="display:block;font-size:12px;color:#64748b">Sitemap adresleri (her satıra bir tane; boş bırakırsanız robots.txt ve /sitemap.xml’den otomatik bulunur)<textarea id="g_sm" rows="2">' + esc((c.sitemaps || []).join('\n')) + '</textarea></label>' +
        '<div class="spx-row"><div class="t"><b>Arama performansı</b><small>Tıklama/gösterim/sıralama verisini çek</small></div>' + sw('g_an', c.analytics) + '</div>' +
        '<button class="spx-b p" id="g_cfg">Kaydet</button> ' + (st.connected ? '<button class="spx-b" data-run="sitemap,inspect,analytics">Şimdi çalıştır (hepsi)</button> <button class="spx-b" data-run="sitemap">Sadece sitemap gönder</button> <button class="spx-b" data-run="inspect">Sadece sayfaları denetle</button>' : '') +
        '<div style="margin-top:10px;font-size:13px">Son çalışma: <b>' + fdt(st.last_run) + '</b>' + (st.last_error ? '<div style="color:#b91c1c;margin-top:4px">Hata: ' + esc(st.last_error) + '</div>' : '') +
        (lr.sitemaps ? '<div>Gönderilen sitemap: ' + ((lr.sitemaps.submitted || []).length) + (lr.sitemaps.errors && lr.sitemaps.errors.length ? ' · hata: ' + esc(lr.sitemaps.errors[0]) : '') + ' · sitemap’teki sayfa: ' + (lr.sitemap_urls || 0) + ' · denetlenen: ' + (lr.inspected || 0) + (lr.quota ? ' · ' + esc(lr.quota) : '') + '</div>' : '') + '</div>' +
        '<details style="margin-top:10px"><summary style="cursor:pointer;color:#475569">Sunucu zamanlayıcısı çalışmazsa: cPanel Cron adresi</summary><small style="color:#64748b;display:block;margin:6px 0">cPanel → Cron Jobs → günde 1 kez şu komutu ekleyin:</small><input readonly style="width:100%" onclick="this.select()" value="curl -s \'' + esc(st.cron_url) + '\' >/dev/null"></details></div>';
      /* 3. sitemap durumu, 4. dizin raporu — yer tutucu */
      h += '<div class="spx-card"><b>3 · Google’daki sitemap durumu</b><div id="g_sms" style="margin-top:8px">' + (st.connected ? 'Yükleniyor…' : 'Önce Google’a bağlanın.') + '</div></div>';
      h += '<div class="spx-card"><b>4 · Dizin (indeks) raporu</b> <small style="color:#64748b">Denetlenen: ' + st.inspected + ' · Dizinde: ' + st.indexed + '</small><div id="g_rep" style="margin-top:8px">Yükleniyor…</div>' +
        '<div style="margin-top:10px"><input id="g_url" placeholder="/kombi/ankara/ veya tam adres" style="width:280px"> <button class="spx-b" id="g_chk"' + (st.connected ? '' : ' disabled') + '>Bu sayfayı Google’a sor</button> <span id="g_chk_r" style="margin-left:8px"></span></div></div>';
      body().innerHTML = h;
      var again = function (m) { return function () { if (m) toast(m); drawGsc(); }; };
      if ($('#g_save')) $('#g_save').onclick = function () { call('PUT', '/admin/gsc/client', { client_id: $('#g_cid').value, client_secret: $('#g_cs').value }).then(again('Kaydedildi')).catch(fail); };
      if ($('#g_conn')) $('#g_conn').onclick = function () { call('PUT', '/admin/gsc/client', { client_id: $('#g_cid').value, client_secret: $('#g_cs').value }).then(function () { return call('GET', '/admin/gsc/oauth-url'); }).then(function (r) { var w = window.open(r.url, 'gscauth', 'width=520,height=680'); var done = function () { clearInterval(iv); window.removeEventListener('message', onm); toast('Google bağlandı'); drawGsc(); }; var onm = function (e) { if (e.data === 'gsc-connected') done(); }; window.addEventListener('message', onm); var iv = setInterval(function () { if (!w || w.closed) { clearInterval(iv); window.removeEventListener('message', onm); drawGsc(); } }, 1200); }).catch(fail); };
      if ($('#g_dis')) $('#g_dis').onclick = function () { if (confirm('Google bağlantısı kesilsin mi?')) call('POST', '/admin/gsc/disconnect', {}).then(again('Bağlantı kesildi')).catch(fail); };
      $('#g_cfg').onclick = function () { call('PUT', '/admin/gsc/config', { auto: $('#g_auto').checked, analytics: $('#g_an').checked, interval_h: +$('#g_int').value, inspect_per_run: +$('#g_ins').value, sitemaps: $('#g_sm').value.split(/\s+/).filter(Boolean) }).then(again('Kaydedildi')).catch(fail); };
      body().onclick = function (e) { var b = e.target.closest('[data-run]'); if (!b) return; var all = body().querySelectorAll('[data-run]'); Array.prototype.forEach.call(all, function (x) { x.disabled = true; }); toast('Çalışıyor… (birkaç dakika sürebilir)'); call('POST', '/admin/gsc/run', { parts: b.getAttribute('data-run').split(',') }).then(again('Tamamlandı')).catch(function (er) { fail(er); drawGsc(); }); };
      if ($('#g_chk')) $('#g_chk').onclick = function () { var u = $('#g_url').value.trim(); if (!u) return; $('#g_chk_r').textContent = 'Soruluyor…'; call('POST', '/admin/gsc/inspect-url', { path: u }).then(function (r) { $('#g_chk_r').innerHTML = '<b style="color:' + (r.verdict === 'PASS' ? '#15803d' : '#b45309') + '">' + esc(r.state || r.verdict || 'Bilinmiyor') + '</b>' + (r.last_crawl ? ' · son tarama ' + fdt(r.last_crawl) : ''); }).catch(function (er) { $('#g_chk_r').textContent = ''; fail(er); }); };
      call('GET', '/admin/gsc/index-report').then(function (r) {
        $('#g_rep').innerHTML = r.total ? '<div style="margin-bottom:8px">' + r.states.map(function (x) { return '<span class="spx-pill" style="margin:2px">' + esc(x[0]) + ': ' + x[1] + '</span>'; }).join(' ') + '</div>' + (r.problems.length ? '<table><tr><th>Dizinde olmayan sayfa</th><th>Durum</th><th>Son tarama</th></tr>' + r.problems.map(function (p) { return '<tr><td>' + esc(p.path) + '</td><td>' + esc(p.state || p.verdict) + '</td><td>' + fdt(p.last_crawl) + '</td></tr>'; }).join('') + '</table>' : '<div style="color:#15803d">Denetlenen tüm sayfalar dizinde ✓</div>') : 'Henüz denetim yapılmadı. “Şimdi çalıştır” ile başlatın.';
      }).catch(function () { $('#g_rep').textContent = 'Rapor alınamadı'; });
      if (st.connected) {
        call('GET', '/admin/gsc/sites').then(function (r) { var sel = $('#g_prop'); if (!sel) return; sel.innerHTML = r.sites.map(function (x) { return '<option value="' + esc(x.siteUrl) + '"' + (x.siteUrl === r.selected ? ' selected' : '') + '>' + esc(x.siteUrl) + ' (' + esc(x.permissionLevel) + ')</option>'; }).join('') || '<option>Mülk bulunamadı</option>'; sel.onchange = function () { call('PUT', '/admin/gsc/config', { property: sel.value }).then(function () { toast('Mülk seçildi'); }).catch(fail); }; }).catch(function (er) { var sel = $('#g_prop'); if (sel) sel.outerHTML = '<span style="color:#b91c1c">' + esc(er.message) + '</span>'; });
        call('GET', '/admin/gsc/sitemaps').then(function (r) { $('#g_sms').innerHTML = r.length ? '<table><tr><th>Sitemap</th><th>Son gönderim</th><th>Gönderilen</th><th>Dizinde</th><th>Hata</th><th>Uyarı</th><th></th></tr>' + r.map(function (s) { var sub = 0, ind = 0; s.contents.forEach(function (x) { sub += x.submitted; ind += x.indexed; }); return '<tr><td>' + esc(s.path) + '</td><td>' + fdt(s.last_submitted) + '</td><td>' + sub + '</td><td>' + ind + '</td><td style="color:' + (s.errors ? '#b91c1c' : 'inherit') + '">' + s.errors + '</td><td>' + s.warnings + '</td><td><button class="spx-b d" data-sd="' + esc(s.path) + '">Sil</button></td></tr>'; }).join('') + '</table>' : 'Google’da kayıtlı sitemap yok. “Şimdi çalıştır” sitemap’i gönderir.'; $('#g_sms').onclick = function (e) { var d = e.target.closest('[data-sd]'); if (d && confirm('Sitemap Google’dan kaldırılsın mı?')) call('DELETE', '/admin/gsc/sitemaps?path=' + encodeURIComponent(d.getAttribute('data-sd'))).then(function () { toast('Silindi'); drawGsc(); }).catch(fail); }; }).catch(function (er) { $('#g_sms').innerHTML = '<span style="color:#b91c1c">' + esc(er.message) + '</span>'; });
      }
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }

  /* --- gelişmiş ürün yönetimi --- */
  var PF = { q: '', brand: '', category: '', active: '', price_min: '', price_max: '', stock: '', source: '', no_price: '', no_image: '', featured: '', sort: 'new', page: 1, per: 50 };
  var PSEL = {}, PALL = false, PDATA = null;
  function drawProducts() {
    var u = Object.keys(PF).filter(function (k) { return PF[k] !== '' && PF[k] !== null; }).map(function (k) { return k + '=' + encodeURIComponent(PF[k]); }).join('&');
    call('GET', '/admin/shop-products/search?' + u).then(function (r) {
      PDATA = r; var st = r.stats;
      var chip = function (label, n, patch, on) { return '<button class="spx-b' + (on ? ' p' : '') + '" data-pf=\'' + JSON.stringify(patch) + '\' style="margin:2px">' + label + ' <b>' + n + '</b></button>'; };
      var h = '<div class="spx-card"><div>' + chip('Tümü', st.all, { active: '', no_price: '', source: '' }, !PF.active && !PF.no_price && !PF.source) + chip('Yayında', st.active, { active: '1', no_price: '', source: '' }, PF.active === '1') + chip('Pasif', st.passive, { active: '0', no_price: '', source: '' }, PF.active === '0') + chip('Fiyatı yok', st.no_price, { no_price: '1', active: '', source: '' }, PF.no_price === '1') + chip('Markadan çekilen', st.imported, { source: 'imported', active: '', no_price: '' }, PF.source === 'imported') + '</div>' +
        '<div class="spx-g" style="margin-top:10px"><label>Ara (ad, model, kod)<input id="pf_q" value="' + esc(PF.q) + '" placeholder="örn. nitromix"></label>' +
        '<label>Marka<select id="pf_brand"><option value="">Tüm markalar</option>' + r.brands.map(function (b) { return '<option value="' + esc(b.name) + '"' + (PF.brand === b.name ? ' selected' : '') + '>' + esc(b.name) + ' (' + b.count + ')</option>'; }).join('') + '</select></label>' +
        '<label>Kategori<select id="pf_cat"><option value="">Tüm kategoriler</option>' + r.categories.map(function (b) { return '<option value="' + esc(b.name) + '"' + (PF.category === b.name ? ' selected' : '') + '>' + esc(b.name) + ' (' + b.count + ')</option>'; }).join('') + '</select></label>' +
        '<label>Fiyat en az ₺<input id="pf_pmin" type="number" value="' + esc(PF.price_min) + '"></label><label>Fiyat en çok ₺<input id="pf_pmax" type="number" value="' + esc(PF.price_max) + '"></label>' +
        '<label>Stok<select id="pf_stock"><option value="">Hepsi</option><option value="in"' + (PF.stock === 'in' ? ' selected' : '') + '>Stokta</option><option value="out"' + (PF.stock === 'out' ? ' selected' : '') + '>Tükenmiş</option></select></label>' +
        '<label>Sırala<select id="pf_sort"><option value="new">En yeni</option><option value="upd">Son güncellenen</option><option value="name">Ada göre</option><option value="brand">Markaya göre</option><option value="asc">Fiyat artan</option><option value="desc">Fiyat azalan</option></select></label>' +
        '<label>Sayfada<select id="pf_per"><option>25</option><option>50</option><option>100</option><option>200</option></select></label></div>' +
        '<div style="margin-top:8px"><label style="margin-right:14px"><input type="checkbox" id="pf_ni"' + (PF.no_image ? ' checked' : '') + '> Görseli olmayanlar</label><label style="margin-right:14px"><input type="checkbox" id="pf_ft"' + (PF.featured ? ' checked' : '') + '> Öne çıkanlar</label> <button class="spx-b p" id="pf_go">Filtrele</button> <button class="spx-b" id="pf_clr">Temizle</button> <span style="margin-left:10px;color:#64748b">' + r.total + ' ürün bulundu</span></div></div>';
      var pageIds = r.items.map(function (x) { return x.id; }), allOn = pageIds.length && pageIds.every(function (i) { return PSEL[i]; });
      var nsel = PALL ? r.total : Object.keys(PSEL).length;
      h += '<div class="spx-card" id="pbar" style="position:sticky;top:0;z-index:5;' + (nsel ? '' : 'display:none') + '"><b id="psel_n">' + nsel + ' ürün seçili</b> ' + (allOn && !PALL && r.total > r.items.length ? '<button class="spx-b" id="p_all">Filtreye uyan ' + r.total + ' ürünün tamamını seç</button> ' : '') + (PALL ? '<button class="spx-b" id="p_none">Seçimi kaldır</button> ' : '') +
        '<span style="display:inline-block;margin-left:8px"><button class="spx-b p" data-pb="activate">Yayına al</button> <button class="spx-b" data-pb="deactivate">Pasife al</button> <button class="spx-b" data-pb="category">Kategori değiştir</button> <button class="spx-b" data-pb="brand">Marka değiştir</button> <button class="spx-b" data-pb="price_percent">Fiyata % ekle</button> <button class="spx-b" data-pb="price_add">Fiyata ₺ ekle</button> <button class="spx-b" data-pb="feature">Öne çıkar</button> <button class="spx-b" data-pb="unfeature">Öne çıkarmayı kaldır</button> <button class="spx-b d" data-pb="delete">Sil</button></span></div>';
      h += '<div class="spx-card" style="overflow:auto"><table><tr><th><input type="checkbox" id="p_head"' + (allOn ? ' checked' : '') + '></th><th></th><th>Ürün</th><th>Marka</th><th>Kategori</th><th>Fiyat ₺</th><th>Stok</th><th>Yayında</th></tr>' + (r.items.length ? r.items.map(function (x) {
        return '<tr data-id="' + x.id + '"><td><input type="checkbox" class="p_ck"' + ((PSEL[x.id] || PALL) ? ' checked' : '') + '></td><td>' + (x.img ? '<img src="' + esc(x.img) + '" style="width:42px;height:42px;object-fit:contain" loading="lazy" referrerpolicy="no-referrer">' : '') + '</td><td><b>' + esc(x.name) + '</b><small style="display:block;color:#64748b">' + esc(x.model || x.sku || '') + (x.imported ? ' · markadan' : '') + (x.featured ? ' · ★' : '') + '</small></td><td>' + esc(x.brand) + '</td><td>' + esc(x.category) + '</td><td><input class="p_pr" type="number" value="' + (x.price || '') + '" style="width:100px"></td><td>' + (x.track_stock ? x.stock : '∞') + '</td><td><div style="display:flex">' + sw('p_a' + x.id, x.active) + '</div></td></tr>';
      }).join('') : '<tr><td colspan="8">Bu filtreye uyan ürün yok.</td></tr>') + '</table>';
      var pages = Math.ceil(r.total / r.per);
      if (pages > 1) h += '<div style="margin-top:10px;display:flex;gap:6px;align-items:center;flex-wrap:wrap"><button class="spx-b" data-pp="' + Math.max(1, r.page - 1) + '">‹</button> Sayfa <b>' + r.page + '</b> / ' + pages + ' <button class="spx-b" data-pp="' + Math.min(pages, r.page + 1) + '">›</button></div>';
      h += '</div>';
      body().innerHTML = h;
      $('#pf_sort').value = PF.sort; $('#pf_per').value = String(PF.per);
      var apply = function () { PF.q = $('#pf_q').value.trim(); PF.brand = $('#pf_brand').value; PF.category = $('#pf_cat').value; PF.price_min = $('#pf_pmin').value; PF.price_max = $('#pf_pmax').value; PF.stock = $('#pf_stock').value; PF.sort = $('#pf_sort').value; PF.per = +$('#pf_per').value; PF.no_image = $('#pf_ni').checked ? '1' : ''; PF.featured = $('#pf_ft').checked ? '1' : ''; PF.page = 1; PSEL = {}; PALL = false; drawProducts(); };
      $('#pf_go').onclick = apply; $('#pf_q').onkeydown = function (e) { if (e.key === 'Enter') apply(); };
      ['pf_brand', 'pf_cat', 'pf_stock', 'pf_sort', 'pf_per', 'pf_ni', 'pf_ft'].forEach(function (i) { $('#' + i).onchange = apply; });
      $('#pf_clr').onclick = function () { PF = { q: '', brand: '', category: '', active: '', price_min: '', price_max: '', stock: '', source: '', no_price: '', no_image: '', featured: '', sort: 'new', page: 1, per: 50 }; PSEL = {}; PALL = false; drawProducts(); };
      var upd = function () { var n = PALL ? r.total : Object.keys(PSEL).length; var bar = $('#pbar'); if (bar) { bar.style.display = n ? '' : 'none'; $('#psel_n').textContent = n + ' ürün seçili'; } };
      $('#p_head').onchange = function () { var on = this.checked; pageIds.forEach(function (i) { if (on) PSEL[i] = 1; else delete PSEL[i]; }); if (!on) PALL = false; drawProducts(); };
      if ($('#p_all')) $('#p_all').onclick = function () { PALL = true; drawProducts(); };
      if ($('#p_none')) $('#p_none').onclick = function () { PALL = false; PSEL = {}; drawProducts(); };
      body().onclick = function (e) {
        var b = e.target.closest('[data-pf]'); if (b) { var pt = JSON.parse(b.getAttribute('data-pf')); for (var k in pt) PF[k] = pt[k]; PF.page = 1; PSEL = {}; PALL = false; return drawProducts(); }
        b = e.target.closest('[data-pp]'); if (b) { PF.page = +b.getAttribute('data-pp'); return drawProducts(); }
        b = e.target.closest('[data-pb]'); if (b) return bulk(b.getAttribute('data-pb'));
      };
      body().onchange = function (e) {
        var tr = e.target.closest('tr[data-id]'); if (!tr) return; var id = tr.getAttribute('data-id');
        if (e.target.classList.contains('p_ck')) { if (e.target.checked) PSEL[id] = 1; else { delete PSEL[id]; PALL = false; } return upd(); }
        if (e.target.classList.contains('p_pr')) { var v = +e.target.value; return call('PUT', '/shop/products/' + id, { price: v }).then(function () { toast('Fiyat kaydedildi'); }).catch(fail); }
        if (e.target.type === 'checkbox' && e.target.id && e.target.id.indexOf('p_a') === 0) { var on = e.target.checked; return call('POST', '/admin/shop-products/bulk', { ids: [id], action: on ? 'activate' : 'deactivate' }).then(function (x) { if (on && x.skipped_no_price) { e.target.checked = false; toast('Fiyatı olmayan ürün yayına alınamaz'); } else toast('Kaydedildi'); }).catch(fail); }
      };
      function bulk(act) {
        var n = PALL ? PDATA.total : Object.keys(PSEL).length; if (!n) return toast('Önce ürün seçin');
        var val = null, msg = n + ' ürüne uygulansın mı?';
        if (act === 'category') { val = prompt('Yeni kategori adı:'); if (!val) return; }
        if (act === 'brand') { val = prompt('Yeni marka adı:'); if (!val) return; }
        if (act === 'price_percent') { val = prompt('Fiyatlara yüzde ekle (indirim için eksi yazın, örn. 10 veya -5):'); if (val === null || val === '') return; }
        if (act === 'price_add') { val = prompt('Fiyatlara TL ekle (örn. 250 veya -100):'); if (val === null || val === '') return; }
        if (act === 'delete') { if (!confirm(n + ' ürün KALICI olarak silinecek. Emin misiniz?')) return; } else if (!confirm(msg)) return;
        var payload = PALL ? { filter: { q: PF.q, brand: PF.brand, category: PF.category, active: PF.active, price_min: PF.price_min, price_max: PF.price_max, no_price: PF.no_price, stock: PF.stock, source: PF.source, no_image: PF.no_image, featured: PF.featured }, action: act, value: val } : { ids: Object.keys(PSEL), action: act, value: val };
        call('POST', '/admin/shop-products/bulk', payload).then(function (x) { toast(x.changed + ' ürün güncellendi' + (x.skipped_no_price ? ' (' + x.skipped_no_price + ' ürün fiyatsız olduğu için yayına alınmadı)' : '')); PSEL = {}; PALL = false; drawProducts(); }).catch(fail);
      }
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }

  /* --- marka merkezi (kolay mod) --- */
  var HPOLL = null;
  function drawBrand() {
    clearInterval(HPOLL); clearInterval(BPOLL);
    call('GET', '/admin/brand-hub').then(function (r) {
      var rows = r.brands, q = r.queue || {}, tot = 0, act = 0, np = 0; rows.forEach(function (b) { tot += b.count; act += b.active; np += b.no_price; });
      body().innerHTML = '<div class="spx-card"><b>Marka Ürün Aktarma</b> <small style="color:#64748b">Sitedeki ' + rows.length + ' markanın resmi sitesinden tüm modeller (başlık, açıklama, özellik, görsel) çekilir; üstüne kâr oranı eklenir.</small>' +
        '<div class="spx-g" style="margin:10px 0;align-items:end"><label>Kâr oranı % (tüm markalar)<input id="h_mp" type="number" value="20"></label><label>Yuvarlama ₺<input id="h_rt" type="number" value="10"></label><div><button class="spx-b" id="h_mk" style="width:100%">Oranı tüm ürünlere uygula</button></div></div>' +
        '<div class="spx-row"><div class="t"><b>Her 24 saatte otomatik güncelle</b><small>Tüm markalar sunucuda kendiliğinden çekilir (fiyatını elle girdiğiniz ürünlere dokunulmaz). Son otomatik çalışma: ' + (r.cfg && r.cfg.last_done ? fdt(r.cfg.last_done) + ' · ' + r.cfg.last_ok + '/' + r.cfg.last_total + ' marka ürün verdi' : 'henüz yok') + '</small></div>' + sw('h_auto', !r.cfg || r.cfg.auto) + '</div><div><button class="spx-b p" id="h_all">⟳ ŞİMDİ TÜM MARKALARI GÜNCELLE</button> <button class="spx-b" id="h_pub">Fiyatı olan ürünleri yayına al</button> <span id="h_st" style="margin-left:8px;font-size:13px"></span></div>' +
        '<div style="margin-top:8px;font-size:13px;color:#475569">Toplam <b>' + tot + '</b> ürün · yayında <b>' + act + '</b> · fiyatı girilmemiş <b>' + np + '</b>. Marka siteleri fiyat yayınlamıyorsa ürünler pasif gelir: markanın satırından “Ürünler / fiyat”a girip liste fiyatı yazın veya Excel yapıştırın.</div></div>' +
        '<div class="spx-card" style="overflow:auto"><table><tr><th>Marka</th><th>Marka sitesi adresi</th><th>Ürün</th><th>Yayında</th><th>Kâr %</th><th>Son durum</th><th></th></tr>' + rows.map(function (b) {
          return '<tr data-s="' + b.slug + '"><td><b>' + esc(b.name) + '</b></td><td><input class="h_url" value="' + esc(b.site_url) + '" placeholder="Resmi site bulunamadı — adres yazın" style="width:240px"></td><td>' + b.count + '</td><td>' + b.active + '</td><td><input class="h_pc" type="number" value="' + b.markup_percent + '" style="width:62px"></td><td style="font-size:12px;color:#64748b">' + (b.state === 'running' ? '⏳ çalışıyor' : (b.last_run ? fdt(b.last_run) + (b.last && b.last.found !== undefined ? ' · ' + b.last.found + ' ürün' : '') + (b.last && b.last.error ? ' · hata' : '') : '—')) + '</td><td style="white-space:nowrap"><button class="spx-b" data-hr="' + b.slug + '">Güncelle</button> <button class="spx-b" data-hp="' + b.slug + '"' + (b.id ? '' : ' disabled') + '>Ürünler / fiyat</button> <button class="spx-b" data-hd="' + b.slug + '" title="Siteye ulaşılıyor mu, kaç ürün adresi görünüyor?">Tanı</button></td></tr>';
        }).join('') + '</table></div>' +
        '<div class="spx-card"><button class="spx-b" id="h_adv">Gelişmiş: özel liste adresi / Demirdöküm kategori kaynakları</button></div>';
      var setSt = function (q) { var e = $('#h_st'); if (!e) return clearInterval(HPOLL); if (q.state === 'running') { e.textContent = '⏳ ' + q.current + ' (' + q.done + '/' + q.total + ')'; } else if (q.state === 'done' && Object.keys(q.log || {}).length) { var bad = Object.keys(q.log).filter(function (k) { return !/^\d+ ürün$/.test(q.log[k]) || q.log[k] === '0 ürün'; }); e.textContent = 'Bitti' + (bad.length ? ' · sorunlu: ' + bad.map(function (k) { return k + ' (' + q.log[k] + ')'; }).slice(0, 6).join(', ') + (bad.length > 6 ? '…' : '') : ''); } };
      var poll = function () { call('GET', '/admin/brand-hub').then(function (r2) { setSt(r2.queue); if (r2.queue.state !== 'running') { clearInterval(HPOLL); HPOLL = null; if (TAB === 'marka' && $('#h_st')) { var keep = $('#h_st').textContent; drawBrand(); setTimeout(function () { var e = $('#h_st'); if (e) setSt(r2.queue); }, 300); } } }).catch(function () { clearInterval(HPOLL); }); };
      if (q.state === 'running') { setSt(q); HPOLL = setInterval(poll, 3000); } else setSt(q);
      var start = function (slugs) { call('POST', '/admin/brand-hub/run', { slugs: slugs }).then(function (x) { toast(x.already ? 'Zaten çalışıyor' : 'Güncelleme başladı — sayfayı kapatsanız da sunucuda devam eder'); clearInterval(HPOLL); HPOLL = setInterval(poll, 3000); setTimeout(poll, 600); }).catch(fail); };
      $('#h_all').onclick = function () { if (confirm('Tüm markalar sırayla güncellenecek. Bu uzun sürebilir (arka planda çalışır). Başlatılsın mı?')) start([]); };
      $('#h_pub').onclick = function () { call('POST', '/admin/brand-hub/publish', {}).then(function (x) { toast(x.activated + ' ürün yayına alındı'); drawBrand(); }).catch(fail); };
      $('#h_mk').onclick = function () { call('POST', '/admin/brand-hub/markup', { percent: +$('#h_mp').value, round_to: +$('#h_rt').value }).then(function (x) { toast(x.repriced + ' ürünün fiyatı güncellendi'); drawBrand(); }).catch(fail); };
      $('#h_adv').onclick = drawBrandAdv;
      $('#h_auto').onchange = function () { call('PUT', '/admin/brand-hub-cfg', { auto: this.checked, interval_h: 24 }).then(function () { toast('Kaydedildi'); }).catch(fail); };
      body().onclick = function (e) {
        var b = e.target.closest('[data-hr]'); if (b) { var tr = b.closest('tr'); return call('PUT', '/admin/brand-hub/' + b.getAttribute('data-hr'), { site_url: tr.querySelector('.h_url').value, markup_percent: +tr.querySelector('.h_pc').value }).then(function () { start([b.getAttribute('data-hr')]); }).catch(fail); }
        b = e.target.closest('[data-hp]'); if (b) { var sid = rows.filter(function (x) { return x.slug === b.getAttribute('data-hp'); })[0].id; BSEL = sid; return drawBrandAdv(); }
      };
      body().onchange = function (e) { var tr = e.target.closest('tr[data-s]'); if (!tr || !(e.target.classList.contains('h_url') || e.target.classList.contains('h_pc'))) return; call('PUT', '/admin/brand-hub/' + tr.getAttribute('data-s'), { site_url: tr.querySelector('.h_url').value, markup_percent: +tr.querySelector('.h_pc').value }).then(function () { toast('Kaydedildi'); }).catch(fail); };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }

  /* --- marka ürün aktarma --- */
  var BSEL = null, BPOLL = null;
  function drawBrandAdv() {
    clearInterval(BPOLL);
    call('GET', '/admin/brand-sources').then(function (r) {
      var src = r.sources || [];
      if (!BSEL || !src.some(function (x) { return x.id === BSEL; })) BSEL = src.length ? src[0].id : null;
      var h = '<div class="spx-card"><button class="spx-b" data-bhub="1">← Marka listesine dön</button> <b>Gelişmiş: marka kaynakları</b> <small style="color:#64748b">Marka sitesindeki ürünleri (başlık, açıklama, teknik özellik, görsel) çeker; üzerine kâr oranınızı ekler.</small><div style="margin:8px 0">' +
        src.map(function (x) { return '<button class="spx-b' + (x.id === BSEL ? ' p' : '') + '" data-bs="' + x.id + '" style="margin:2px">' + esc(x.name) + ' (' + x.product_count + ')</button>'; }).join(' ') +
        ' <button class="spx-b" data-bnew="1" style="margin:2px">+ Yeni kaynak</button> <button class="spx-b p" data-ball="1" style="margin:2px">+ Demirdöküm: TÜM kategorileri ekle</button> ' + (src.length ? '<button class="spx-b p" data-brunall="1" style="margin:2px">⟳ Tüm kaynakları güncelle</button> ' : '') + '<details style="margin-top:6px"><summary style="cursor:pointer;color:#64748b">tek tek hazır ayarlar</summary>' + (r.presets || []).map(function (p, i) { return '<button class="spx-b" data-bpre="' + i + '" style="margin:2px">+ ' + esc(p.name) + '</button>'; }).join(' ') + '</details></div></div><div id="b_main"></div>';
      body().innerHTML = h;
      body().onclick = function (e) {
        var b = e.target.closest('[data-bhub]'); if (b) return drawBrand();
        b = e.target.closest('[data-bs]'); if (b) { BSEL = b.getAttribute('data-bs'); return drawBrandAdv(); }
        b = e.target.closest('[data-ball]'); if (b) { var have = src.map(function (x) { return x.name; }); var todo = (r.presets || []).filter(function (p) { return have.indexOf(p.name) < 0; }); if (!todo.length) return toast('Hepsi zaten ekli'); b.disabled = true; return todo.reduce(function (pr, p) { return pr.then(function () { return call('POST', '/admin/brand-sources', p); }); }, Promise.resolve()).then(function () { toast(todo.length + ' kategori eklendi — şimdi “Tüm kaynakları güncelle”ye basın'); drawBrandAdv(); }).catch(fail); }
        b = e.target.closest('[data-brunall]'); if (b) { b.disabled = true; return src.reduce(function (pr, x) { return pr.then(function () { return call('POST', '/admin/brand-sources/' + x.id + '/run', {}); }); }, Promise.resolve()).then(function () { toast('Güncelleme başladı; her kaynağı seçip ilerlemeyi görebilirsiniz'); b.disabled = false; }).catch(fail); }
        b = e.target.closest('[data-bnew]'); if (b) return brandForm(null, {});
        b = e.target.closest('[data-bpre]'); if (b) return brandForm(null, r.presets[+b.getAttribute('data-bpre')]);
      };
      var cur = src.filter(function (x) { return x.id === BSEL; })[0];
      if (cur) brandMain(cur); else $('#b_main').innerHTML = '<div class="spx-card">Henüz kaynak yok. Yukarıdan “Demirdöküm hazır ayarı”nı veya “+ Yeni kaynak”ı seçin.</div>';
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  function brandForm(cur, d) {
    d = d || {}; var c = cur || {}; var v = function (k, def) { return esc(d[k] !== undefined ? d[k] : (c[k] !== undefined ? c[k] : def)); };
    $('#b_main').innerHTML = '<div class="spx-card"><b>' + (cur ? 'Kaynağı düzenle' : 'Yeni kaynak') + '</b><div class="spx-g" style="margin:8px 0"><label>Kaynak adı<input id="f_name" value="' + v('name', '') + '"></label><label>Marka (mağazada görünen)<input id="f_brand" value="' + v('brand', '') + '"></label><label>Kategori<input id="f_cat" value="' + v('category', '') + '"></label>' +
      '<label>Kâr oranı %<input id="f_mp" type="number" value="' + v('markup_percent', 20) + '"></label><label>Ek sabit tutar ₺<input id="f_mf" type="number" value="' + v('markup_fixed', 0) + '"></label><label>Yuvarlama (₺)<input id="f_rt" type="number" value="' + v('round_to', 10) + '"></label><label>En çok ürün<input id="f_mx" type="number" value="' + v('max_products', 150) + '"></label></div>' +
      '<label style="display:block;font-size:12px;color:#64748b">Ürün listesi/kategori adresleri (her satıra bir tane)<textarea id="f_urls" rows="3">' + esc((d.start_urls || c.start_urls || []).join('\n')) + '</textarea></label>' +
      '<div class="spx-g" style="margin:8px 0"><label>Sitemap adresi (isteğe bağlı)<input id="f_sm" value="' + v('sitemap_url', '') + '"></label><label>Ürün adresi deseni (regex, isteğe bağlı)<input id="f_re" value="' + v('link_regex', '') + '"></label></div>' +
      '<div class="spx-row"><div class="t"><b>Haftada bir otomatik güncelle</b></div>' + sw('f_aw', c.auto_weekly) + '</div><div class="spx-row"><div class="t"><b>Yeni ürünler (fiyatı varsa) hemen yayına alınsın</b></div>' + sw('f_na', c.new_active) + '</div>' +
      '<button class="spx-b p" id="f_save">Kaydet</button> <button class="spx-b" id="f_cancel">Vazgeç</button></div>';
    $('#f_cancel').onclick = drawBrandAdv;
    $('#f_save').onclick = function () {
      var p = { name: $('#f_name').value, brand: $('#f_brand').value, category: $('#f_cat').value, markup_percent: +$('#f_mp').value, markup_fixed: +$('#f_mf').value, round_to: +$('#f_rt').value, max_products: +$('#f_mx').value, start_urls: $('#f_urls').value.split(/\s+/).filter(Boolean), sitemap_url: $('#f_sm').value, link_regex: $('#f_re').value, auto_weekly: $('#f_aw').checked, new_active: $('#f_na').checked };
      call(cur ? 'PUT' : 'POST', '/admin/brand-sources' + (cur ? '/' + cur.id : ''), p).then(function (x) { BSEL = x.id || (cur && cur.id); toast('Kaydedildi'); drawBrandAdv(); }).catch(fail);
    };
  }
  function brandMain(s) {
    var lr = s.last_result || {};
    $('#b_main').innerHTML = '<div class="spx-card"><b>' + esc(s.name) + '</b> <span class="spx-pill">' + esc(s.brand) + '</span> <small style="color:#64748b">Kâr: %' + s.markup_percent + (s.markup_fixed ? ' + ' + s.markup_fixed + ' ₺' : '') + ' · son güncelleme: ' + fdt(s.last_run) + (lr.error ? ' · <span style="color:#b91c1c">' + esc(lr.error) + '</span>' : (lr.added !== undefined ? ' · ' + lr.added + ' yeni, ' + lr.updated + ' güncellendi' : '')) + '</small>' +
      '<div style="margin:10px 0"><button class="spx-b p" id="b_run">⟳ Listeyi güncelle</button> <button class="spx-b" id="b_edit">Düzenle</button> <button class="spx-b" id="b_act">Fiyatı olanları yayına al</button> <button class="spx-b d" id="b_del">Kaynağı sil</button> <span id="b_st" style="margin-left:8px;font-size:13px"></span></div>' +
      '<div class="spx-g"><label>Kâr oranı % (tüm ürünlere uygula)<input id="b_mp" type="number" value="' + s.markup_percent + '"></label><label>Ek sabit ₺<input id="b_mf" type="number" value="' + s.markup_fixed + '"></label><label>Yuvarlama ₺<input id="b_rt" type="number" value="' + s.round_to + '"></label><label>&nbsp;<button class="spx-b" id="b_rep" style="width:100%">Oranı tüm ürünlere uygula</button></label></div>' +
      '<details style="margin-top:10px"><summary style="cursor:pointer">Fiyat listesi yükle (Excel’den kopyala: ürün adı veya kod ; liste fiyatı)</summary><textarea id="b_csv" rows="4" placeholder="Nitromix 24 kW;24.500&#10;SKU123;31000"></textarea><input type="file" id="b_file" accept=".csv,.txt"> <button class="spx-b" id="b_csvgo">Fiyatları işle</button> <span id="b_csvr"></span></details></div>' +
      '<div class="spx-card"><b>Ürünler</b> <small style="color:#64748b">Liste fiyatını yazın → satış fiyatı otomatik hesaplanır. Fiyatı olmayan ürünler yayında görünmez.</small><div id="b_tab" style="margin-top:8px;overflow:auto">Yükleniyor…</div></div>';
    $('#b_edit').onclick = function () { brandForm(s); };
    $('#b_del').onclick = function () { if (confirm('Kaynak silinsin mi?')) { var rm = confirm('Bu kaynaktan eklenen ürünler de mağazadan silinsin mi?\nTamam = ürünleri de sil, İptal = ürünler kalsın'); call('DELETE', '/admin/brand-sources/' + s.id + '?remove_products=' + rm).then(function () { BSEL = null; drawBrandAdv(); }).catch(fail); } };
    $('#b_act').onclick = function () { call('POST', '/admin/brand-sources/' + s.id + '/activate-priced', {}).then(function (r) { toast(r.activated + ' ürün yayına alındı'); loadProducts(s); }).catch(fail); };
    $('#b_rep').onclick = function () { call('POST', '/admin/brand-sources/' + s.id + '/reprice', { markup_percent: +$('#b_mp').value, markup_fixed: +$('#b_mf').value, round_to: +$('#b_rt').value }).then(function (r) { toast(r.repriced + ' ürünün fiyatı güncellendi'); loadProducts(s); }).catch(fail); };
    $('#b_file').onchange = function () { var f = this.files[0]; if (!f) return; var rd = new FileReader(); rd.onload = function () { $('#b_csv').value = rd.result; }; rd.readAsText(f); };
    $('#b_csvgo').onclick = function () { call('POST', '/admin/brand-sources/' + s.id + '/prices-csv', { csv: $('#b_csv').value }).then(function (r) { $('#b_csvr').textContent = r.matched + ' eşleşti' + (r.unmatched ? ', ' + r.unmatched + ' eşleşmedi: ' + r.unmatched_names.slice(0, 5).join(', ') : ''); loadProducts(s); }).catch(fail); };
    var setSt = function (st) { var e = $('#b_st'); if (!e) return clearInterval(BPOLL); e.textContent = st.state === 'running' ? ('⏳ ' + (st.msg || '')) : (st.state === 'error' ? '⚠ ' + st.msg : (st.msg || '')); $('#b_run').disabled = st.state === 'running'; };
    var poll = function () { call('GET', '/admin/brand-sources/' + s.id + '/status').then(function (st) { setSt(st); if (st.state !== 'running') { clearInterval(BPOLL); if (TAB === 'marka' && $('#b_tab') && BPOLL) { BPOLL = null; loadProducts(s); } } }).catch(function () { clearInterval(BPOLL); }); };
    $('#b_run').onclick = function () { call('POST', '/admin/brand-sources/' + s.id + '/run', {}).then(function () { BPOLL = setInterval(poll, 2000); poll(); }).catch(fail); };
    call('GET', '/admin/brand-sources/' + s.id + '/status').then(function (st) { if (st.state === 'running') { BPOLL = setInterval(poll, 2000); setSt(st); } });
    loadProducts(s);
  }
  function loadProducts(s) {
    call('GET', '/admin/brand-sources/' + s.id + '/products').then(function (r) {
      var ps = r.products; var e = $('#b_tab'); if (!e) return;
      e.innerHTML = ps.length ? '<table><tr><th></th><th>Ürün</th><th>Liste fiyatı ₺</th><th>Satış fiyatı ₺</th><th>Yayında</th></tr>' + ps.map(function (p) {
        return '<tr data-id="' + p.id + '"><td>' + (p.image ? '<img src="' + esc(p.image) + '" style="width:44px;height:44px;object-fit:contain" loading="lazy" referrerpolicy="no-referrer">' : '') + '</td><td>' + esc(p.name) + (p.url ? ' <a href="' + esc(p.url) + '" target="_blank" rel="noopener">↗</a>' : '') + '</td><td><input class="bp_b" type="number" value="' + (p.base_price || '') + '" style="width:110px"></td><td><input class="bp_p" type="number" value="' + (p.price || '') + '" style="width:110px" title="Elle yazarsanız oran uygulanmaz"></td><td><div style="display:flex">' + sw('bp_a' + p.id, p.active) + '</div></td></tr>';
      }).join('') + '</table>' : 'Henüz ürün yok. “Listeyi güncelle” ile çekin.';
      e.onchange = function (ev) {
        var tr = ev.target.closest('tr[data-id]'); if (!tr) return; var id = tr.getAttribute('data-id'), body_ = {};
        if (ev.target.classList.contains('bp_b')) body_.base_price = +ev.target.value; else if (ev.target.classList.contains('bp_p')) body_.price = +ev.target.value; else body_.active = ev.target.checked;
        call('PUT', '/admin/brand-products/' + id, body_).then(function (x) { if (body_.base_price !== undefined) tr.querySelector('.bp_p').value = x.price; toast('Kaydedildi'); }).catch(function (er) { fail(er); loadProducts(s); });
      };
    }).catch(fail);
  }

  /* ================= Müşteri 360 · Kaynak analizi · Usta puanlama · Cari & trend ================= */
  var TLf = function (n) { n = +n || 0; return n.toLocaleString('tr-TR', { maximumFractionDigits: 0 }) + ' ₺'; };
  var DT = function (s) { if (!s) return '—'; var d = new Date(s); return isNaN(d) ? '—' : d.toLocaleDateString('tr-TR'); };
  var CHN = { google_ads: 'Google Reklam', meta_ads: 'Meta Reklam', diger_reklam: 'Diğer Reklam', organik: 'Organik (Google vb.)', sosyal: 'Sosyal Medya', referans: 'Başka Site', direkt: 'Direkt', bilinmiyor: 'Bilinmiyor' };
  var LVC = { Platin: '#7c3aed', 'Altın': '#d97706', 'Gümüş': '#64748b', Bronz: '#b45309', 'Gelişim': '#dc2626', Yeni: '#0891b2' };
  function tbl(head, rows, cls) { return '<div style="overflow:auto"><table class="' + (cls || '') + '" style="width:100%;border-collapse:collapse;font-size:13px"><thead><tr>' + head.map(function (h) { return '<th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e2e8f0;color:#64748b;font-weight:600;white-space:nowrap">' + h + '</th>'; }).join('') + '</tr></thead><tbody>' + (rows.length ? rows.join('') : '<tr><td colspan="' + head.length + '" style="padding:14px;color:#64748b">Kayıt yok</td></tr>') + '</tbody></table></div>'; }
  function tr_(cells, attr) { return '<tr ' + (attr || '') + ' style="' + (attr ? 'cursor:pointer;' : '') + '">' + cells.map(function (c) { return '<td style="padding:7px 8px;border-bottom:1px solid #eef2f6;vertical-align:top">' + c + '</td>'; }).join('') + '</tr>'; }
  function pill(t, c) { return '<span class="spx-pill" style="' + (c ? 'background:' + c + ';color:#fff' : '') + '">' + esc(t) + '</span>'; }
  function bar(p, c) { p = Math.max(0, Math.min(100, +p || 0)); return '<div style="background:#e2e8f0;border-radius:6px;height:8px;min-width:70px"><div style="width:' + p + '%;height:8px;border-radius:6px;background:' + (c || (p >= 80 ? '#16a34a' : p >= 60 ? '#f59e0b' : '#dc2626')) + '"></div></div>'; }
  function stat(l, v, sub) { return '<div class="spx-card" style="margin:0"><small style="color:#64748b">' + l + '</small><div class="spx-stat">' + v + '</div>' + (sub ? '<small style="color:#64748b">' + sub + '</small>' : '') + '</div>'; }
  function grid(items) { return '<div class="spx-g" style="margin-bottom:14px">' + items.join('') + '</div>'; }

  /* --- Müşteri 360 --- */
  var M360 = { q: '', seg: '' };
  function drawM360() {
    var qs = '?q=' + encodeURIComponent(M360.q) + '&segment=' + encodeURIComponent(M360.seg);
    call('GET', '/customers360' + qs).then(function (d) {
      var sg = d.segments || {};
      var h = '<div class="spx-card"><div class="spx-g"><label>Ara (ad / telefon / il)<input id="m3q" value="' + esc(M360.q) + '" placeholder="örn. Ayşe, 0532…"></label><label>Segment<select id="m3s"><option value="">Hepsi (' + d.total + ')</option>' + ['VIP', 'Sadık', 'Yeni', 'Aday', 'Pasif'].map(function (s) { return '<option value="' + s + '"' + (M360.seg === s ? ' selected' : '') + '>' + s + ' (' + (sg[s] || 0) + ')</option>'; }).join('') + '</select></label></div>' +
        '<small style="color:#64748b;display:block;margin-top:8px">VIP: 3+ tamamlanan iş veya 5.000 ₺+ ciro · Sadık: 2 iş · Yeni: 1 iş · Aday: talep etmiş ama iş açılmamış · Pasif: 1 yıldır işi yok. Bir müşteriye tıklayın: hangi kanaldan geldi, neyi aradı, hangi sayfaları gezdi, tüm işleri ve notları.</small></div><div class="spx-card">' +
        tbl(['Müşteri', 'Segment', 'İş', 'Ciro', 'Ort. sepet', 'Puan', 'Geliş kanalı', 'Aranan / sayfa', 'Son iş'], d.rows.map(function (r) {
          return tr_([esc(r.name || '—') + '<small>' + esc(r.phone || '') + (r.city ? ' · ' + esc(r.city) : '') + '</small>', pill(r.segment), r.done + '/' + r.jobs, TLf(r.revenue) + (r.open_balance > 0 ? '<small style="color:#dc2626">açık ' + TLf(r.open_balance) + '</small>' : ''), r.avg_ticket ? TLf(r.avg_ticket) : '—', r.rating ? '★ ' + r.rating : '—', esc(CHN[r.channel] || r.channel || '—'), esc(r.term || r.landing || '—'), DT(r.last_job_at)], 'data-k="' + esc(r.key) + '"');
        })) + '</div>';
      body().innerHTML = h;
      $('#m3q').onchange = function () { M360.q = this.value; drawM360(); }; $('#m3s').onchange = function () { M360.seg = this.value; drawM360(); };
      body().onclick = function (e) { var tr = e.target.closest('tr[data-k]'); if (tr) m360Detail(tr.getAttribute('data-k')); };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  function m360Detail(key) {
    body().innerHTML = 'Yükleniyor…';
    call('GET', '/customers360/' + encodeURIComponent(key)).then(function (d) {
      var s = d.summary, c = d.customer || {};
      var h = '<div style="margin-bottom:10px"><button class="spx-b" id="m3b">← Listeye dön</button></div><div class="spx-card"><b style="font-size:18px">' + esc(c.name || '—') + '</b> ' + pill(s.segment) + '<small style="display:block;color:#64748b">' + esc(d.phone || '') + (c.email ? ' · ' + esc(c.email) : '') + (c.address ? ' · ' + esc(c.address) : '') + '</small></div>' +
        grid([stat('Toplam ciro', TLf(s.revenue), s.done + ' tamamlanan iş'), stat('Ort. sepet', s.avg_ticket ? TLf(s.avg_ticket) : '—'), stat('Açık bakiye', TLf(s.open_balance), s.open_balance > 0 ? 'tahsil edilmemiş' : 'borcu yok'), stat('İşler arası', s.avg_gap_days != null ? s.avg_gap_days + ' gün' : '—', 'ilk temas ' + DT(s.first_contact))]);
      if (d.suggestions.length) h += '<div class="spx-card" style="border-color:#f59e0b"><b>Fırsat</b><br>' + d.suggestions.map(esc).join('<br>') + '</div>';
      h += '<div class="spx-card"><b>Siteye geliş yolculuğu</b><small style="display:block;color:#64748b;margin-bottom:6px">Talep formunu doldurduğu andaki oturumdan alınır.</small>' + (d.journeys.length ? d.journeys.map(function (j) {
        return '<div class="spx-row" style="align-items:flex-start"><div class="t"><b>' + esc(CHN[j.channel] || j.channel || '—') + '</b> ' + (j.source ? '<small style="display:inline">· ' + esc(j.source) + '</small>' : '') + (j.campaign ? ' · kampanya: ' + esc(j.campaign) : '') + (j.term ? '<br>Reklam anahtar kelimesi: <b>' + esc(j.term) + '</b>' : '') + '<small>' + DT(j.first_seen) + ' · ' + esc(j.device || '') + ' · ' + Math.round((j.duration_sec || 0) / 60) + ' dk · ilk sayfa ' + esc(j.landing || '') + (j.referrer ? ' · gelen: ' + esc(j.referrer.slice(0, 60)) : '') + '</small>' +
          (j.searches.length ? '<div style="margin-top:4px">Sitede aradığı: ' + j.searches.map(function (x) { return pill(x.q); }).join(' ') + '</div>' : '') + '<small>Gezdiği sayfalar: ' + (j.pages.map(function (p) { return esc(p.path); }).join(' → ') || '—') + '</small></div></div>';
      }).join('') : '<small style="color:#64748b">Bu müşteri için kayıtlı site oturumu yok (telefonla veya takip kodundan önce gelmiş olabilir).</small>') + '</div>';
      h += '<div class="spx-card"><b>İşler</b>' + tbl(['No', 'Tarih', 'Cihaz / arıza', 'Usta', 'Tutar', 'Tahsilat', 'Puan'], d.jobs.map(function (j) { return tr_([esc(j.job_number || ''), DT(j.created_at), esc(j.device) + '<small>' + esc(j.fault) + '</small>', esc(j.tech || '—'), TLf(j.total), j.payment_status === 'veresiye' ? pill('Veresiye', '#dc2626') : j.payment_status === 'kismi' ? pill('Kısmi', '#f59e0b') : (j.status === 'tamamlandi' || j.status === 'faturalandi' ? pill('Tahsil', '#16a34a') : '—'), j.rating ? '★ ' + j.rating + (j.comment ? '<small>' + esc(j.comment) + '</small>' : '') : '—']); })) + '</div>';
      h += '<div class="spx-card"><b>Notlar</b><div style="display:flex;gap:8px;margin:8px 0"><input id="m3n" style="flex:1" placeholder="Not ekle (örn. kapıyı çalmayın, aramayı tercih eder)"><button class="spx-b p" id="m3a">Ekle</button></div>' + d.notes.map(function (n) { return '<div class="spx-row"><div class="t">' + esc(n.text) + '<small>' + esc(n.by) + ' · ' + DT(n.at) + '</small></div></div>'; }).join('') + '</div>';
      body().innerHTML = h;
      $('#m3b').onclick = drawM360; $('#m3a').onclick = function () { var t = $('#m3n').value.trim(); if (!t) return; call('POST', '/customers360/' + encodeURIComponent(d.phone || key) + '/note', { text: t }).then(function () { m360Detail(key); }).catch(fail); };
    }).catch(function (e) { fail(e); drawM360(); });
  }

  /* --- Kaynak & arama analizi --- */
  var KDAYS = 90;
  function drawKaynak() {
    call('GET', '/analytics/sources?days=' + KDAYS).then(function (d) {
      var rt = function (rows, nm, extra) { return tbl([nm, 'Talep', 'Tamamlanan', 'Ciro', 'Ort. sepet'].concat(extra ? ['Ziyaret', 'Dönüşüm'] : []), rows.map(function (r) { return tr_([esc(CHN[r.name] || r.name), r.leads, r.done, '<b>' + TLf(r.revenue) + '</b>', r.avg_ticket ? TLf(r.avg_ticket) : '—'].concat(extra ? [r.visits || 0, r.conv_pct != null ? '%' + r.conv_pct : '—'] : [])); })); };
      var h = '<div class="spx-card"><div class="spx-g"><label>Dönem<select id="kd">' + [30, 90, 180, 365].map(function (x) { return '<option value="' + x + '"' + (x === KDAYS ? ' selected' : '') + '>Son ' + x + ' gün</option>'; }).join('') + '</select></label></div><small style="color:#64748b;display:block;margin-top:6px">' + esc(d.note) + '</small></div>' +
        grid([stat('Ziyaret', d.visits), stat('Talep', d.leads), stat('Site içi arama', d.site_search.total)]) +
        '<div class="spx-card"><b>Kanallar — hangi kaynak para kazandırıyor?</b>' + rt(d.channels, 'Kanal', true) + '</div>' +
        '<div class="spx-card"><b>Reklam anahtar kelimeleri</b>' + rt(d.keywords, 'Anahtar kelime') + '</div>' +
        '<div class="spx-card"><b>İlk girilen sayfalar</b>' + rt(d.pages, 'Sayfa') + '</div>' +
        '<div class="spx-card"><b>Cihaz türüne göre</b>' + rt(d.devices, 'Cihaz') + '</div>' +
        '<div class="spx-card"><b>Ziyaretçiler sitede ne aradı?</b><div class="spx-g" style="grid-template-columns:repeat(auto-fit,minmax(260px,1fr))"><div>' + tbl(['Arama', 'Kez'], d.site_search.top.map(function (r) { return tr_([esc(r.q), r.n]); })) + '</div><div><b style="color:#dc2626">Sonuç bulunamayanlar (içerik eksiği)</b>' + tbl(['Arama', 'Kez'], d.site_search.zero_result.map(function (r) { return tr_([esc(r.q), r.n]); })) + '</div></div></div>';
      body().innerHTML = h; $('#kd').onchange = function () { KDAYS = +this.value; drawKaynak(); };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }

  /* --- Usta puanlama --- */
  var UDAYS = 90;
  function drawUstaPuan() {
    call('GET', '/tech-rating?days=' + UDAYS).then(function (d) {
      var h = '<div class="spx-card"><div class="spx-g"><label>Dönem<select id="ud">' + [30, 90, 180, 365].map(function (x) { return '<option value="' + x + '"' + (x === UDAYS ? ' selected' : '') + '>Son ' + x + ' gün</option>'; }).join('') + '</select></label></div>' +
        '<small style="color:#64748b;display:block;margin-top:8px">Puan 0-100: ' + d.weights.map(function (w) { return w.label + ' %' + w.weight; }).join(' · ') + '. Cironun puana etkisi yoktur (usta fazla ücret almaya yönelmesin). Verisi olmayan bölüm hesaba katılmaz. 5 işten az olan usta “Yeni” sayılır. Seviyeler: Platin 90+, Altın 80+, Gümüş 70+, Bronz 55+, altı Gelişim.</small></div><div class="spx-card">' +
        tbl(['#', 'Usta', 'Puan', 'Seviye', 'Tamam / İptal', 'Müşteri ★', 'Tekrar arıza', 'Ort. süre', 'Ciro', 'Zayıf yön'], d.rows.map(function (r) {
          return tr_([r.rank, '<b>' + esc(r.name) + '</b>' + (r.is_active === false ? ' <small>(pasif)</small>' : ''), '<b style="font-size:16px">' + r.score + '</b>' + bar(r.score), pill(r.level, LVC[r.level]), r.done + ' / ' + r.cancelled, r.rating_n ? '★ ' + r.rating_avg + ' (' + r.rating_n + ')' : '—', r.redo, r.avg_hours ? r.avg_hours + ' sa' : '—', TLf(r.revenue), esc(r.weak.map(function (w) { return w.label; }).join(', ') || '—')], 'data-k="' + esc(r.id) + '"');
        })) + '</div>';
      body().innerHTML = h; $('#ud').onchange = function () { UDAYS = +this.value; drawUstaPuan(); };
      body().onclick = function (e) { var tr = e.target.closest('tr[data-k]'); if (tr) ustaDetail(tr.getAttribute('data-k')); };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }

  /* --- usta iş geçmişi (menü: Ustalar → Usta İş Geçmişi) : filtre, sıralama, sayfalama, CSV, ayrıntı --- */
  var UG = { days: '90', from: '', to: '', city: '', dist: '', grp: '', act: '', dev: '', brand: '', q: '', sort: 'done', page: 1 }, UGM = null, UGR = [];
  var UGSORT = [['done', 'Tamamlanan (çoktan aza)'], ['total', 'Toplam iş'], ['revenue', 'Ciro'], ['rating', 'Müşteri puanı'], ['rate', 'Tamamlama %'], ['open', 'Açık iş'], ['idle', 'Uzun süredir iş almayan'], ['balance', 'Bakiye (borç)'], ['name', 'İsim']];
  var UGDAYS = [['30', 'Son 30 gün'], ['90', 'Son 90 gün'], ['180', 'Son 6 ay'], ['365', 'Son 1 yıl'], ['0', 'Tüm zamanlar'], ['x', 'Özel aralık…']];
  var DEVL = { kombi: 'Kombi', klima: 'Klima', buzdolabi: 'Buzdolabı', 'camasir-makinesi': 'Çamaşır mak.', 'bulasik-makinesi': 'Bulaşık mak.', televizyon: 'Televizyon', sofben: 'Şofben', ocak: 'Ocak', firin: 'Fırın', diger: 'Diğer' };
  var fD = function (s) { if (!s) return '—'; var d = new Date(s); return isNaN(d) ? '—' : d.toLocaleDateString('tr-TR'); };
  var fN = function (n) { return (+n || 0).toLocaleString('tr-TR'); };
  function ugQs(o) {
    var p = [];
    if (o.days === 'x') { if (o.from) p.push('date_from=' + o.from); if (o.to) p.push('date_to=' + o.to); } else if (+o.days) p.push('days=' + o.days);
    return p;
  }
  function dlCsv(name, head, rows) {
    var q = function (v) { v = v == null ? '' : String(v); return /[";\n,]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var t = '﻿' + [head].concat(rows).map(function (r) { return r.map(q).join(';'); }).join('\r\n');
    var a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([t], { type: 'text/csv;charset=utf-8' })); a.download = name; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }
  function ugOpt(list, cur) { return list.map(function (x) { return '<option value="' + esc(x[0]) + '"' + (String(x[0]) === String(cur) ? ' selected' : '') + '>' + esc(x[1]) + '</option>'; }).join(''); }
  function drawUstaGecmis() {
    var qs = ugQs(UG); ['city', 'dist', 'grp', 'act', 'dev', 'brand', 'q'].forEach(function (k) { if (UG[k]) qs.push((k === 'dist' ? 'district' : k === 'grp' ? 'group' : k === 'act' ? 'active' : k === 'dev' ? 'device_type' : k) + '=' + encodeURIComponent(UG[k])); });
    var kept = document.activeElement && document.activeElement.id;
    Promise.all([call('GET', '/technicians-history' + (qs.length ? '?' + qs.join('&') : '')), UGM ? Promise.resolve(UGM) : call('GET', '/jobs/meta').catch(function () { return { brands: [], types: [] }; })]).then(function (a) {
      var rows = a[0]; UGM = a[1]; UGR = rows;
      var S = UG.sort, ix = function (r) { return r.idle_days == null ? -1 : r.idle_days; };
      var list = rows.slice().sort(function (x, y) {
        return S === 'name' ? x.name.localeCompare(y.name, 'tr') : S === 'total' ? y.total - x.total : S === 'revenue' ? y.revenue - x.revenue : S === 'rating' ? (y.rating - x.rating) || (y.rating_n - x.rating_n) : S === 'rate' ? ((y.done_rate == null ? -1 : y.done_rate) - (x.done_rate == null ? -1 : x.done_rate)) : S === 'open' ? y.open - x.open : S === 'idle' ? (x.total ? 0 : 1) - (y.total ? 0 : 1) || (ix(y) - ix(x)) : S === 'balance' ? y.balance - x.balance : (y.done - x.done) || (y.total - x.total);
      });
      var sum = rows.reduce(function (s, r) { s.t += r.total; s.d += r.done; s.o += r.open; s.c += r.cancelled; s.rev += r.revenue; if (r.rating_n) { s.rs += r.rating * r.rating_n; s.rn += r.rating_n; } if (r.is_active !== false && (r.idle_days == null || r.idle_days >= 30)) s.idle++; if (r.balance > 0) s.bal += r.balance; return s; }, { t: 0, d: 0, o: 0, c: 0, rev: 0, rs: 0, rn: 0, idle: 0, bal: 0 });
      var PG = 25, pages = Math.max(1, Math.ceil(list.length / PG)); if (UG.page > pages) UG.page = pages;
      var vis = list.slice((UG.page - 1) * PG, UG.page * PG);
      var types = (UGM.types || []).map(function (t) { return [t, DEVL[t] || t]; }), brands = (UGM.brands || []).map(function (b) { return [b, b]; });
      var dl = UG.city ? (TRD[trCity(UG.city)] || []) : [];
      var sel = 'border:1px solid #cbd5e1;border-radius:8px;padding:7px;font-size:13px;background:#fff;min-width:0;width:100%';
      var lab = function (t, c) { return '<label style="font-size:12px;color:#64748b;font-weight:600">' + t + c + '</label>'; };
      var h = '<div class="spx-card"><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px">' +
        lab('Dönem', '<select id="ug_days" style="' + sel + '">' + ugOpt(UGDAYS, UG.days) + '</select>') +
        (UG.days === 'x' ? lab('Başlangıç', '<input type="date" id="ug_from" value="' + esc(UG.from) + '" style="' + sel + '">') + lab('Bitiş', '<input type="date" id="ug_to" value="' + esc(UG.to) + '" style="' + sel + '">') : '') +
        lab('İl', '<select id="ug_city" style="' + sel + '"><option value="">Tüm iller</option>' + ugOpt(TRK.map(function (c) { return [c, c]; }), UG.city) + '</select>') +
        lab('İlçe', '<select id="ug_dist" style="' + sel + '"' + (UG.city ? '' : ' disabled') + '><option value="">Tüm ilçeler</option>' + ugOpt(dl.map(function (c) { return [c, c]; }), UG.dist) + '</select>') +
        lab('Servis grubu', '<select id="ug_grp" style="' + sel + '"><option value="">Tümü</option>' + ugOpt(TGRP, UG.grp) + '</select>') +
        lab('Durum', '<select id="ug_act" style="' + sel + '">' + ugOpt([['', 'Aktif + pasif'], ['1', 'Sadece aktif'], ['0', 'Sadece pasif']], UG.act) + '</select>') +
        lab('Cihaz türü (işlerde)', '<select id="ug_dev" style="' + sel + '"><option value="">Tümü</option>' + ugOpt(types, UG.dev) + '</select>') +
        lab('Marka (işlerde)', '<select id="ug_brand" style="' + sel + '"><option value="">Tümü</option>' + ugOpt(brands, UG.brand) + '</select>') +
        lab('Ara', '<input id="ug_q" value="' + esc(UG.q) + '" placeholder="Usta adı, il, ilçe" style="' + sel + '">') +
        lab('Sırala', '<select id="ug_sort" style="' + sel + '">' + ugOpt(UGSORT, UG.sort) + '</select>') +
        '</div><div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center"><button class="spx-b" id="ug_clr">Filtreleri temizle</button><button class="spx-b" id="ug_csv">⬇ Excel (CSV) indir</button><small style="color:#64748b">Filtreler hem ustaları hem iş sayılarını etkiler: dönem, cihaz ve marka işlerin tarihine/türüne göre sayılır.</small></div></div>' +
        grid([stat('Usta', fN(rows.length), 'filtreye uyan'), stat('Toplam iş', fN(sum.t), 'tamamlanan ' + fN(sum.d) + ' · açık ' + fN(sum.o) + ' · iptal ' + fN(sum.c)), stat('Ciro', TLf(sum.rev), 'tamamlanan işler'), stat('Ort. müşteri puanı', sum.rn ? (sum.rs / sum.rn).toFixed(1) + ' ★' : '—', sum.rn + ' değerlendirme'), stat('30+ gün iş almayan', fN(sum.idle), 'aktif ustalar'), stat('Ustalardaki borç', TLf(sum.bal), 'şirkete ödenmemiş')]) +
        '<div class="spx-card"><small style="color:#64748b;display:block;margin-bottom:8px">' + list.length + ' usta · satıra tıklayınca ustanın tüm geçmişi (aylık dağılım, cihaz/marka/bölge kırılımı, ödemeler, iş listesi) açılır.</small>' +
        tbl(['Usta', 'Bölge / grup', 'Toplam', 'Tamam.', '%', 'Bu ay', 'Açık', 'İptal', 'Ciro', 'Süre', '★', 'Bakiye', 'Son iş'], vis.map(function (r) {
          var idle = r.idle_days == null ? '<span style="color:#94a3b8">hiç iş yok</span>' : r.idle_days >= 60 ? '<span style="color:#dc2626">' + r.idle_days + ' gün önce</span>' : r.idle_days >= 30 ? '<span style="color:#d97706">' + r.idle_days + ' gün önce</span>' : fD(r.last);
          return tr_(['<b>' + esc(r.name) + '</b>' + (r.is_active === false ? ' <small>(pasif)</small>' : '') + '<small style="display:block;color:#64748b">' + esc(r.phone || '') + '</small>',
            esc(r.place || '—') + '<small style="display:block;color:#64748b">' + esc((r.groups || []).map(function (g) { var f = TGRP.filter(function (x) { return x[0] === g; })[0]; return f ? f[1] : g; }).join(', ')) + '</small>',
            r.total, '<b style="color:#15803d">' + r.done + '</b>', r.done_rate == null ? '—' : '%' + r.done_rate, r.month, r.open ? '<b style="color:#c2570c">' + r.open + '</b>' : 0, r.cancelled, r.revenue ? TLf(r.revenue) : '—', r.avg_hours == null ? '—' : (r.avg_hours < 48 ? Math.round(r.avg_hours) + ' sa' : Math.round(r.avg_hours / 24) + ' gün'),
            r.rating_n ? '★ ' + r.rating + ' <small>(' + r.rating_n + ')</small>' : '—', r.balance ? '<b style="color:' + (r.balance > 0 ? '#dc2626' : '#15803d') + '">' + TLf(r.balance) + '</b>' : '—', idle], 'data-k="' + esc(r.id) + '"');
        })) +
        (pages > 1 ? '<div style="display:flex;gap:8px;align-items:center;justify-content:center;margin-top:10px"><button class="spx-b" data-pg="-1"' + (UG.page <= 1 ? ' disabled' : '') + '>‹ Önceki</button><span style="font-size:13px">Sayfa ' + UG.page + ' / ' + pages + '</span><button class="spx-b" data-pg="1"' + (UG.page >= pages ? ' disabled' : '') + '>Sonraki ›</button></div>' : '') + '</div>';
      body().innerHTML = h;
      var re = function () { UG.page = 1; drawUstaGecmis(); };
      [['days', 'ug_days'], ['from', 'ug_from'], ['to', 'ug_to'], ['grp', 'ug_grp'], ['act', 'ug_act'], ['dev', 'ug_dev'], ['brand', 'ug_brand']].forEach(function (p) { var e = $('#' + p[1]); if (e) e.onchange = function () { UG[p[0]] = this.value; re(); }; });
      $('#ug_city').onchange = function () { UG.city = this.value; UG.dist = ''; re(); };
      $('#ug_dist').onchange = function () { UG.dist = this.value; re(); };
      $('#ug_sort').onchange = function () { UG.sort = this.value; UG.page = 1; drawUstaGecmis(); };
      var qi = $('#ug_q'); qi.onkeydown = function (e) { if (e.key === 'Enter') { UG.q = this.value.trim(); re(); } }; qi.onchange = function () { UG.q = this.value.trim(); re(); };
      $('#ug_clr').onclick = function () { UG = { days: '90', from: '', to: '', city: '', dist: '', grp: '', act: '', dev: '', brand: '', q: '', sort: UG.sort, page: 1 }; drawUstaGecmis(); };
      $('#ug_csv').onclick = function () { dlCsv('usta-gecmis-' + new Date().toISOString().slice(0, 10) + '.csv', ['Usta', 'Telefon', 'Aktif', 'İl', 'İlçeler', 'Servis grupları', 'Toplam iş', 'Tamamlanan', 'Tamamlama %', 'Bu ay', 'Açık', 'İptal', 'Ciro', 'Ort. iş süresi (saat)', 'Müşteri puanı', 'Değerlendirme sayısı', 'Bakiye (borç)', 'Son iş', 'İş almayan gün'], list.map(function (r) { return [r.name, r.phone, r.is_active === false ? 'Pasif' : 'Aktif', r.city, (r.districts || []).join(', '), (r.groups || []).join(', '), r.total, r.done, r.done_rate == null ? '' : r.done_rate, r.month, r.open, r.cancelled, r.revenue, r.avg_hours == null ? '' : r.avg_hours, r.rating || '', r.rating_n, r.balance, r.last ? r.last.slice(0, 10) : '', r.idle_days == null ? '' : r.idle_days]; })); };
      body().onclick = function (e) { var pb = e.target.closest('button[data-pg]'); if (pb) { UG.page += +pb.getAttribute('data-pg'); drawUstaGecmis(); return; } var t = e.target.closest('tr[data-k]'); if (t) ustaGecmisDetay(t.getAttribute('data-k')); };
      if (kept === 'ug_q') { var z = $('#ug_q'); if (z) { z.focus(); z.setSelectionRange(z.value.length, z.value.length); } }
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  var UJ = { st: '', dev: '', brand: '', q: '', page: 1, days: null, from: '', to: '' };
  function ustaGecmisDetay(id, keep) {
    if (!keep) UJ = { st: '', dev: '', brand: '', q: '', page: 1, days: UG.days, from: UG.from, to: UG.to };
    var per = ugQs({ days: UJ.days, from: UJ.from, to: UJ.to }), pq = per.join('&');
    var jq = per.slice(); ['st', 'dev', 'brand', 'q'].forEach(function (k) { if (UJ[k]) jq.push((k === 'st' ? 'status' : k === 'dev' ? 'device_type' : k) + '=' + encodeURIComponent(UJ[k])); });
    var wasQ = document.activeElement && document.activeElement.id === 'uj_q';
    Promise.all([call('GET', '/technicians-history/' + encodeURIComponent(id) + (pq ? '?' + pq : '')), call('GET', '/technicians-history/' + encodeURIComponent(id) + '/jobs?limit=25&page=' + UJ.page + (jq.length ? '&' + jq.join('&') : ''))]).then(function (a) {
      var d = a[0], J = a[1], sc = d.status_counts || {}, done = (sc.tamamlandi || 0) + (sc.faturalandi || 0), canc = sc.iptal || 0, tot = Object.keys(sc).reduce(function (s, k) { return s + sc[k]; }, 0), open = tot - done - canc;
      var rev = (d.months || []).reduce(function (s, m) { return s + m.revenue; }, 0), pf = d.profile || {};
      var mx = Math.max.apply(null, [1].concat((d.months || []).map(function (m) { return m.total; })));
      var sel = 'border:1px solid #cbd5e1;border-radius:8px;padding:7px;font-size:13px;background:#fff;min-width:0;width:100%';
      var lab = function (t, c) { return '<label style="font-size:12px;color:#64748b;font-weight:600">' + t + c + '</label>'; };
      var ST = [['', 'Tüm durumlar'], ['done', 'Tamamlanan'], ['open', 'Açık'], ['iptal', 'İptal'], ['yeni', 'Yeni'], ['atandi', 'Atandı'], ['yolda', 'Yolda'], ['basladi', 'Başladı']];
      var types = (UGM && UGM.types || []).map(function (t) { return [t, DEVL[t] || t]; }), brands = (UGM && UGM.brands || []).map(function (b) { return [b, b]; });
      var brk = function (t, arr) { var m = Math.max.apply(null, [1].concat(arr.map(function (x) { return x.count; }))); return '<div class="spx-card" style="margin:0"><b>' + t + '</b>' + (arr.length ? arr.map(function (x) { return '<div style="display:flex;align-items:center;gap:8px;margin-top:6px;font-size:13px"><span style="width:42%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(DEVL[x.name] || x.name) + '</span><div style="flex:1">' + bar(100 * x.count / m, '#1d4ed8') + '</div><b>' + x.count + '</b></div>'; }).join('') : '<div style="color:#94a3b8;margin-top:6px">Veri yok</div>') + '</div>'; };
      var h = '<div class="spx-card"><button class="spx-b" id="uj_back">← Tüm ustalar</button> <b style="font-size:18px;margin-left:8px">' + esc(d.name) + '</b>' + (d.is_active === false ? ' ' + pill('Pasif', '#64748b') : '') +
        '<div style="margin-top:6px;font-size:13px;color:#475569">' + [d.phone && '📞 ' + esc(d.phone), d.email && esc(d.email), (pf.city || (pf.districts || []).length) && '📍 ' + esc([pf.city, (pf.districts || []).join(', ')].filter(Boolean).join(' · ')), (pf.service_groups || []).length && '🔧 ' + esc(pf.service_groups.map(function (g) { var f = TGRP.filter(function (x) { return x[0] === g; })[0]; return f ? f[1] : g; }).join(', ')), pf.experience_years && pf.experience_years + ' yıl deneyim', d.created_at && 'Kayıt: ' + fD(d.created_at)].filter(Boolean).join(' · ') + '</div>' +
        (d.note ? '<div style="margin-top:6px;font-size:13px;background:#fffbeb;border-radius:8px;padding:6px 10px">📝 ' + esc(d.note) + '</div>' : '') +
        '<div style="margin-top:10px;max-width:260px">' + lab('Dönem (özet + liste)', '<select id="uj_days" style="' + sel + '">' + ugOpt(UGDAYS, UJ.days) + '</select>') + '</div>' +
        (UJ.days === 'x' ? '<div style="display:flex;gap:8px;margin-top:8px;max-width:420px">' + lab('Başlangıç', '<input type="date" id="uj_from" value="' + esc(UJ.from) + '" style="' + sel + '">') + lab('Bitiş', '<input type="date" id="uj_to" value="' + esc(UJ.to) + '" style="' + sel + '">') + '</div>' : '') + '</div>' +
        grid([stat('Toplam iş', fN(tot), 'tamamlanan ' + fN(done) + ' · açık ' + fN(open) + ' · iptal ' + fN(canc)), stat('Tamamlama oranı', done + canc ? '%' + Math.round(100 * done / (done + canc)) : '—', 'tamamlanan / (tamamlanan+iptal)'), stat('Ciro (son 12 ay)', TLf(rev), 'tamamlanan işler'), stat('Bakiye', '<span style="color:' + (d.balance > 0 ? '#dc2626' : '#15803d') + '">' + TLf(d.balance) + '</span>', 'borç ' + TLf(d.debt_total) + ' · ödenen ' + TLf(d.paid_total)), stat('Komisyon', d.commission_percent ? '%' + d.commission_percent : '—')]) +
        '<div class="spx-card"><b>Aylık dağılım (son 12 ay)</b><div style="display:flex;align-items:flex-end;gap:6px;height:130px;margin-top:10px;overflow-x:auto">' + (d.months || []).map(function (m) { return '<div style="flex:1;min-width:38px;text-align:center;font-size:11px"><div style="height:' + Math.max(3, Math.round(90 * m.total / mx)) + 'px;background:#dbeafe;border-radius:4px 4px 0 0;position:relative" title="Toplam ' + m.total + ' · tamamlanan ' + m.done + '"><div style="position:absolute;bottom:0;left:0;right:0;height:' + (m.total ? Math.round(100 * m.done / m.total) : 0) + '%;background:#16a34a;border-radius:4px 4px 0 0"></div></div><b>' + m.done + '/' + m.total + '</b><div style="color:#64748b">' + m.month.slice(5) + '/' + m.month.slice(2, 4) + '</div><div style="color:#64748b">' + (m.revenue ? Math.round(m.revenue / 1000) + 'k₺' : '') + '</div></div>'; }).join('') + '</div><small style="color:#64748b">Yeşil: tamamlanan · mavi: toplam · altta tamamlanan/toplam ve ciro</small></div>' +
        '<div class="spx-g" style="margin-bottom:14px">' + brk('Cihaz türleri', d.devices || []) + brk('Markalar', d.brands || []) + brk('Müşteri bölgeleri', d.districts || []) + '</div>' +
        '<div class="spx-card"><b>Ödeme / borç / prim hareketleri</b>' + tbl(['Tarih', 'Tür', 'Tutar', 'Açıklama'], (d.cash || []).map(function (x) { return tr_([fD(x.date), x.type === 'teknisyen_borc' ? pill('Borç', '#dc2626') : x.type === 'teknisyen_odeme' ? pill('Ödeme', '#16a34a') : pill('Prim', '#1d4ed8'), '<b>' + TLf(x.amount) + '</b>', esc(x.description || '')]); })) + '</div>' +
        '<div class="spx-card"><b>İş listesi</b><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;margin:10px 0">' +
        lab('Durum', '<select id="uj_st" style="' + sel + '">' + ugOpt(ST, UJ.st) + '</select>') + lab('Cihaz', '<select id="uj_dev" style="' + sel + '"><option value="">Tümü</option>' + ugOpt(types, UJ.dev) + '</select>') + lab('Marka', '<select id="uj_brand" style="' + sel + '"><option value="">Tümü</option>' + ugOpt(brands, UJ.brand) + '</select>') + lab('Ara', '<input id="uj_q" value="' + esc(UJ.q) + '" placeholder="Kayıt no, müşteri, adres, arıza" style="' + sel + '">') + '</div>' +
        '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px"><small style="color:#64748b"><b>' + fN(J.total) + '</b> kayıt bulundu</small><button class="spx-b" id="uj_csv">⬇ Bu listeyi CSV indir</button></div>' +
        tbl(['Kayıt', 'Tarih', 'Tamamlanma', 'Müşteri', 'Adres', 'Cihaz', 'Arıza', 'Tutar', 'Durum'], (J.rows || []).map(function (j) { return tr_(['<b style="color:#1d4ed8">' + esc(j.job_number) + '</b>', fD(j.created_at), j.completed_at ? fD(j.completed_at) : '—', esc(j.customer_name || '') + '<small style="display:block;color:#64748b">' + esc(j.customer_phone || '') + '</small>', esc((j.customer_address || '').slice(0, 50)), esc([j.device_brand_name, DEVL[j.device_type] || j.device_type].filter(Boolean).join(' ')), esc((j.fault_description || '').slice(0, 60)), j.total_amount ? TLf(j.total_amount) : '—', esc(STL[j.status] || j.status)], 'data-j="' + esc(j.id) + '"'); })) +
        (J.total > J.limit ? '<div style="display:flex;gap:8px;align-items:center;justify-content:center;margin-top:10px"><button class="spx-b" data-pg="-1"' + (UJ.page <= 1 ? ' disabled' : '') + '>‹ Önceki</button><span style="font-size:13px">Sayfa ' + UJ.page + ' / ' + Math.ceil(J.total / J.limit) + '</span><button class="spx-b" data-pg="1"' + (UJ.page >= Math.ceil(J.total / J.limit) ? ' disabled' : '') + '>Sonraki ›</button></div>' : '') + '</div>';
      body().innerHTML = h;
      var re = function () { UJ.page = 1; ustaGecmisDetay(id, true); };
      $('#uj_back').onclick = drawUstaGecmis;
      [['days', 'uj_days'], ['from', 'uj_from'], ['to', 'uj_to'], ['st', 'uj_st'], ['dev', 'uj_dev'], ['brand', 'uj_brand']].forEach(function (p) { var e = $('#' + p[1]); if (e) e.onchange = function () { UJ[p[0]] = this.value; re(); }; });
      var qi = $('#uj_q'); qi.onkeydown = function (e) { if (e.key === 'Enter') { UJ.q = this.value.trim(); re(); } }; qi.onchange = function () { UJ.q = this.value.trim(); re(); };
      if (wasQ) { qi.focus(); qi.setSelectionRange(qi.value.length, qi.value.length); }
      $('#uj_csv').onclick = function () { call('GET', '/technicians-history/' + encodeURIComponent(id) + '/jobs?export=true&limit=5000' + (jq.length ? '&' + jq.join('&') : '')).then(function (r) { dlCsv('usta-isleri-' + d.name.replace(/\s+/g, '-') + '.csv', ['Kayıt no', 'Tarih', 'Tamamlanma', 'Müşteri', 'Telefon', 'Adres', 'Cihaz', 'Marka', 'Model', 'Arıza', 'Tutar', 'Durum'], (r.rows || []).map(function (j) { return [j.job_number, (j.created_at || '').slice(0, 10), (j.completed_at || '').slice(0, 10), j.customer_name, j.customer_phone, j.customer_address, DEVL[j.device_type] || j.device_type, j.device_brand_name, j.device_model, j.fault_description, j.total_amount || '', STL[j.status] || j.status]; })); }).catch(fail); };
      body().onclick = function (e) { var pb = e.target.closest('button[data-pg]'); if (pb) { UJ.page += +pb.getAttribute('data-pg'); ustaGecmisDetay(id, true); return; } var t = e.target.closest('tr[data-j]'); if (t) { ov.classList.remove('on'); goto('/admin/jobs/' + t.getAttribute('data-j')); } };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  function ustaDetail(id) {
    body().innerHTML = 'Yükleniyor…';
    call('GET', '/tech-rating/' + id).then(function (d) {
      var t = d.tech;
      var h = '<div style="margin-bottom:10px"><button class="spx-b" id="ub">← Listeye dön</button></div><div class="spx-card"><b style="font-size:18px">' + esc(t.name) + '</b> ' + pill(t.level, LVC[t.level]) + ' <b style="font-size:20px;margin-left:8px">' + t.score + '</b>/100 <small style="display:inline">· sıra ' + t.rank + '</small></div>' +
        '<div class="spx-card"><b>Puan bileşenleri (son 90 gün)</b>' + t.components.map(function (c) { return '<div class="spx-row"><div class="t">' + esc(c.label) + '<small>ağırlık %' + c.weight + '</small></div><div style="width:55%">' + bar(c.value) + '</div><b style="width:44px;text-align:right">' + c.value + '</b></div>'; }).join('') + '</div>' +
        (t.weak.length ? '<div class="spx-card" style="border-color:#f59e0b"><b>Gelişim önerisi</b>' + t.weak.map(function (w) { return '<div style="margin-top:6px"><b>' + esc(w.label) + ':</b> ' + esc(w.tip) + '</div>'; }).join('') + '</div>' : '') +
        '<div class="spx-card"><b>Aylık gidişat</b>' + tbl(['Ay', 'Puan', 'Tamamlanan', 'Müşteri ★'], d.history.map(function (r) { return tr_([r.label, '<b>' + r.score + '</b> ' + bar(r.score), r.done, r.rating || '—']); })) + '</div>' +
        '<div class="spx-card"><b>Düşük puanlı işler</b>' + tbl(['İş', 'Puan', 'Yorum'], d.low_rated.map(function (r) { return tr_([esc(r.job_number || '') + '<small>' + esc(r.device || '') + ' · ' + DT(r.at) + '</small>', '★ ' + r.rating, esc(r.comment || '—')]); })) + '</div>' +
        '<div class="spx-card"><b>Yönetici notları (övgü / uyarı)</b><div class="spx-g" style="margin:8px 0"><label>Tür<select id="un_k"><option>övgü</option><option>uyarı</option><option>not</option></select></label><label style="grid-column:span 2">Not<input id="un_t"></label></div><button class="spx-b p" id="un_a">Ekle</button><small style="display:block;color:#64748b;margin-top:6px">Övgü ve notlar ustaya kendi ekranında görünür; uyarılar sadece yönetimde kalır.</small>' +
        d.notes.map(function (n) { return '<div class="spx-row"><div class="t">' + pill(n.kind, n.kind === 'övgü' ? '#16a34a' : n.kind === 'uyarı' ? '#dc2626' : '') + ' ' + esc(n.text) + '<small>' + esc(n.by) + ' · ' + DT(n.at) + '</small></div></div>'; }).join('') + '</div>';
      body().innerHTML = h; $('#ub').onclick = drawUstaPuan;
      $('#un_a').onclick = function () { var x = $('#un_t').value.trim(); if (!x) return; call('POST', '/tech-rating/' + id + '/note', { kind: $('#un_k').value, text: x }).then(function () { ustaDetail(id); }).catch(fail); };
    }).catch(function (e) { fail(e); drawUstaPuan(); });
  }

  /* ustası seçilmeden girilmiş teknisyen tahsilat/borç kayıtları: usta bakiyesine işlemez → burada ustaya bağlanır */
  function orphanCard() {
    Promise.all([call('GET', '/cash/orphans'), call('GET', '/technicians')]).then(function (a) {
      var o = a[0] || [], T = (a[1] || []).filter(function (t) { return t.is_active !== false; }); if (!o.length || !body()) return;
      var tp = { teknisyen_odeme: 'Şirkete ödeme', teknisyen_borc: 'Tahsilat borcu', teknisyen_prim: 'Prim' };
      var d = document.createElement('div'); d.className = 'spx-card'; d.style.borderColor = '#f59e0b';
      d.innerHTML = '<b>⚠ Ustası seçilmemiş ' + o.length + ' kayıt</b><small style="display:block;color:#64748b;margin:4px 0 8px">Bu hareketlerde teknisyen seçilmediği için usta panelindeki borç/bakiyeye işlenmedi. Ustayı seçip "Ata" deyin.</small>' +
        tbl(['Tarih', 'Tür', 'Tutar', 'Açıklama', 'Usta'], o.map(function (x) { return tr_([DT(x.date), esc(tp[x.type] || x.type), '<b>' + TLf(x.amount) + '</b>', esc(x.description || ''), '<select data-t="' + esc(x.id) + '" style="border:1px solid #cbd5e1;border-radius:8px;padding:5px"><option value="">Usta seç…</option>' + T.map(function (t) { return '<option value="' + esc(t.id) + '">' + esc(t.name) + '</option>'; }).join('') + '</select> <button class="spx-b p" data-as="' + esc(x.id) + '">Ata</button>']); })) ;
      body().insertBefore(d, body().firstChild);
      d.onclick = function (e) { var b = e.target.closest('button[data-as]'); if (!b) return; var id = b.getAttribute('data-as'), sel = d.querySelector('select[data-t="' + id + '"]'); if (!sel.value) { toast('Usta seçin'); return; } call('PUT', '/cash/transactions/' + id, { technician_id: sel.value }).then(function () { toast('Ustaya işlendi'); drawCari(); }).catch(fail); };
    }).catch(function () { });
  }
  /* --- Teknisyen Tahsilat: ustadan alınan parayı gir → usta bakiyesi düşer + muhasebe hareketlerine "Teknisyenden Tahsilat" olarak düşer --- */
  var THALL = false;
  function drawTahsilat() {
    Promise.all([call('GET', '/cash/summary'), call('GET', '/cash/transactions?type=teknisyen_odeme'), call('GET', '/cash/orphans').catch(function () { return []; }), call('GET', '/technicians').catch(function () { return []; })]).then(function (a) {
      var tb = (a[0].technician_balances || []).filter(function (t) { return t.is_active !== false; }), tx = a[1] || [], orp = (a[2] || []).filter(function (x) { return x.type === 'teknisyen_odeme'; }), T = a[3] || [];
      var nm = {}; T.forEach(function (t) { nm[t.id] = t.name; }); tb.forEach(function (t) { nm[t.id] = t.name; });
      var list = tb.map(function (t) { t.rest = t.balance; return t; }).filter(function (t) { return THALL || t.rest > 0; }).sort(function (x, y) { return y.rest - x.rest; });
      var tot = tb.reduce(function (s, t) { return s + Math.max(0, t.rest || (t.debt - t.paid)); }, 0);
      var inp = 'border:1px solid #cbd5e1;border-radius:8px;padding:7px;font-size:13px;background:#fff';
      var h = '<div class="spx-card"><b style="font-size:16px">Teknisyenden tahsilat</b><small style="display:block;color:#64748b;margin:4px 0 8px">Ustadan aldığınız parayı buradan girin. Kayıt hem ustanın bakiyesinden düşer hem de Muhasebe → Hareketler\'e "Teknisyenden Tahsilat" olarak işlenir.</small>' +
        '<label style="font-size:13px"><input type="checkbox" id="th_all"' + (THALL ? ' checked' : '') + '> Borcu olmayan ustaları da göster</label> <b style="float:right">Toplam alacak: ' + TLf(tot) + '</b></div>' +
        (orp.length ? '<div class="spx-card" style="border-color:#f59e0b"><b>⚠ Ustası seçilmemiş ' + orp.length + ' tahsilat kaydı</b><small style="display:block;color:#64748b;margin:4px 0 8px">Bunlar usta bakiyesine işlenmedi. Ustayı seçip "Ata" deyin.</small>' + tbl(['Tarih', 'Tutar', 'Açıklama', 'Usta'], orp.map(function (x) { return tr_([DT(x.date), '<b>' + TLf(x.amount) + '</b>', esc(x.description || ''), '<select data-t="' + esc(x.id) + '" style="' + inp + '"><option value="">Usta seç…</option>' + tb.map(function (t) { return '<option value="' + esc(t.id) + '">' + esc(t.name) + '</option>'; }).join('') + '</select> <button class="spx-b p" data-as="' + esc(x.id) + '">Ata</button>']); })) + '</div>' : '') +
        '<div class="spx-card">' + tbl(['Usta', 'Toplam borç', 'Ödenen', 'Kalan', 'Tahsil edilen tutar', ''], list.map(function (t) {
          return tr_(['<b>' + esc(t.name) + '</b>', TLf(t.debt), TLf(t.paid), '<b style="color:' + (t.rest > 0 ? '#dc2626' : '#15803d') + '">' + TLf(t.rest) + '</b>',
            '<input type="number" min="1" step="0.01" data-a="' + esc(t.id) + '" value="' + (t.rest > 0 ? t.rest : '') + '" placeholder="₺" style="' + inp + ';width:110px"> <select data-m="' + esc(t.id) + '" style="' + inp + '"><option value="nakit">Nakit</option><option value="havale">Havale/EFT</option></select>',
            '<button class="spx-b p" data-go="' + esc(t.id) + '" data-n="' + esc(t.name) + '">Tahsil Et</button>']);
        })) + (list.length ? '' : '<div style="color:#64748b;padding:8px">Borcu olan usta yok.</div>') + '</div>' +
        '<div class="spx-card"><b>Son tahsilatlar</b>' + tbl(['Tarih', 'Usta', 'Tutar', 'Yöntem', 'Açıklama'], tx.slice(0, 30).map(function (x) { return tr_([DT(x.date), esc(nm[x.technician_id] || '— (usta seçilmemiş)'), '<b>' + TLf(x.amount) + '</b>', esc(x.payment_method || ''), esc(x.description || '')]); })) + '</div>';
      body().innerHTML = h;
      $('#th_all').onchange = function () { THALL = this.checked; drawTahsilat(); };
      body().onclick = function (e) {
        var b = e.target.closest('button[data-go]');
        if (b) { var id = b.getAttribute('data-go'), amt = parseFloat(body().querySelector('input[data-a="' + id + '"]').value), m = body().querySelector('select[data-m="' + id + '"]').value; if (!(amt > 0)) { toast('Tutar girin'); return; } if (!confirm(b.getAttribute('data-n') + ' ustadan ' + TLf(amt) + ' tahsil edilsin mi?')) return; b.disabled = true;
          call('POST', '/cash/transactions', { type: 'teknisyen_odeme', technician_id: id, amount: amt, payment_method: m, description: b.getAttribute('data-n') + ' - şirkete tahsilat teslimi' }).then(function () { toast('Tahsilat kaydedildi'); drawTahsilat(); }).catch(function (er) { b.disabled = false; fail(er); }); return; }
        var o = e.target.closest('button[data-as]'); if (o) { var oid = o.getAttribute('data-as'), sel = body().querySelector('select[data-t="' + oid + '"]'); if (!sel.value) { toast('Usta seçin'); return; } call('PUT', '/cash/transactions/' + oid, { technician_id: sel.value }).then(function () { toast('Ustaya işlendi'); drawTahsilat(); }).catch(fail); }
      };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  /* usta panelinde borcu olmayıp fazla ödeme yapmış ustada "Borç yok ₺1.500" yanıltıcı görünüyordu: fazla ödeme açıkça yazılır */
  function balFix() {
    if (!document.body.classList.contains('spx-tech') || !/^\/tech\/balance/.test(location.pathname)) return;
    var m = document.querySelector('main'); if (!m) return;
    var big = [].slice.call(m.querySelectorAll('div,p,span')).filter(function (e) { return e.children.length === 0 && /^₺?\s*[\d.]+,\d\d$/.test(e.textContent.trim()) && /Borç yok|BORÇ YOK/i.test((e.parentElement && e.parentElement.innerText) || ''); })[0];
    if (!big || big.getAttribute('data-bf')) return; big.setAttribute('data-bf', '1');
    var v = big.textContent.trim(); big.textContent = '₺0,00';
    var n = document.createElement('div'); n.style.cssText = 'margin-top:6px;font-size:13px;opacity:.9'; n.textContent = 'Kayıtlı borcunuz yok. Şirkete yaptığınız ' + v + ' ödeme borçtan fazla olduğu için alacak olarak görünür.'; big.parentElement.appendChild(n);
  }
  setInterval(balFix, 800);

  /* --- Cari & trend --- */
  function drawCari() {
    Promise.all([call('GET', '/accounting/trends?months=12'), call('GET', '/accounting/tech-aging'), call('GET', '/accounting/receivables')]).then(function (a) {
      var tr = a[0], ag = a[1], rc = a[2];
      var h = grid([stat('12 ay gelir', TLf(tr.total.income)), stat('12 ay gider', TLf(tr.total.expense)), stat('12 ay net', TLf(tr.total.net)), stat('Müşteri alacağı', TLf(rc.total), 'veresiye/kısmi'), stat('Ustalardaki borç', TLf(ag.total), 'şirkete ödenmemiş')]) +
        '<div class="spx-card"><b>Aylık gidişat</b>' + tbl(['Ay', 'Gelir', 'Gider', 'Net', 'Kâr %', 'İş', 'Ort. sepet', 'Büyüme'], tr.months.map(function (r) { return tr_([r.month, TLf(r.income), TLf(r.expense), '<b style="color:' + (r.net >= 0 ? '#16a34a' : '#dc2626') + '">' + TLf(r.net) + '</b>', '%' + r.margin_pct, r.jobs, r.avg_ticket ? TLf(r.avg_ticket) : '—', r.growth_pct == null ? '—' : (r.growth_pct > 0 ? '▲ %' : '▼ %') + Math.abs(r.growth_pct)]); })) + '</div>' +
        '<div class="spx-card"><b>Gider kalemleri</b>' + tbl(['Kategori', 'Tutar'], tr.expense_by_category.map(function (r) { return tr_([esc(r.category), TLf(r.amount)]); })) + '</div>' +
        '<div class="spx-card"><b>Usta borç yaşlandırma</b><small style="display:block;color:#64748b;margin-bottom:6px">Şirkete borç, ödemeler en eski borca sayılarak (FIFO) yaşlandırılır. 30 günden eski borç ustanın kasa disiplini puanını düşürür.</small>' + tbl(['Usta', 'Toplam', '0-7 gün', '8-30', '31-60', '60+'], ag.rows.map(function (r) { return tr_([esc(r.name), '<b>' + TLf(r.total) + '</b>', TLf(r.b_0_7), TLf(r.b_8_30), '<span style="color:#d97706">' + TLf(r.b_31_60) + '</span>', '<span style="color:#dc2626">' + TLf(r.b_60p) + '</span>']); })) + '</div>' +
        '<div class="spx-card"><b>Müşteri alacakları (veresiye / kısmi)</b><div class="spx-g" style="margin:8px 0"><label>İş numarası<input id="rc_n" placeholder="SRV-…"></label><label>Tutar (tahsilat için)<input id="rc_a" type="number" placeholder="₺"></label></div><button class="spx-b" id="rc_v">Veresiye yap</button> <button class="spx-b p" id="rc_t">Tahsilat gir</button> <button class="spx-b" id="rc_f">Tamamı tahsil edildi</button>' +
        tbl(['İş', 'Müşteri', 'Tutar', 'Tahsil', 'Kalan', 'Gün'], rc.rows.map(function (r) { return tr_([esc(r.job_number || ''), esc(r.customer || '') + '<small>' + esc(r.phone || '') + '</small>', TLf(r.total), TLf(r.collected), '<b>' + TLf(r.open) + '</b>', '<span style="color:' + (r.age_days > 60 ? '#dc2626' : r.age_days > 30 ? '#d97706' : 'inherit') + '">' + r.age_days + '</span>']); })) +
        '<small style="color:#64748b;display:block;margin-top:6px">Yaşlandırma: 0-30 ' + TLf(rc.buckets['0-30']) + ' · 31-60 ' + TLf(rc.buckets['31-60']) + ' · 61-90 ' + TLf(rc.buckets['61-90']) + ' · 90+ ' + TLf(rc.buckets['90+']) + '. Normalde işler tahsil edilmiş sayılır; sadece buradan veresiye işaretlenenler alacak olur.</small></div>';
      body().innerHTML = h; orphanCard();
      var act = function (mode) { var n = $('#rc_n').value.trim(); if (!n) { toast('İş numarası girin'); return; } call('GET', '/accounting/job-lookup?number=' + encodeURIComponent(n)).then(function (j) { return call('PUT', '/accounting/jobs/' + j.id + '/collection', { mode: mode, amount: +$('#rc_a').value || 0 }); }).then(function () { toast('Kaydedildi'); drawCari(); }).catch(fail); };
      $('#rc_v').onclick = function () { act('veresiye'); }; $('#rc_t').onclick = function () { act('tahsilat'); }; $('#rc_f').onclick = function () { act('tamam'); };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }

  /* --- yeni sade menü --- */
  var IC = {
    chart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/></svg>',
    gear: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/></svg>',
    search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>',
    plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></svg>',
    cart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l2.7 12.4a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 2-1.5L21 8H6"/></svg>',
    user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="9" cy="8" r="4"/><path d="M2 21v-1a6 6 0 0 1 6-6h2a6 6 0 0 1 6 6v1M17 11l2 2 4-4"/></svg>',
    moon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
    live: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
  };
  /* [yol | ek:anahtar, etiket] — yol panelin kendi sayfasıdır; ek: bu eklentinin sayfasıdır */
  var MENU = [
    ['', [['/admin', 'Genel Bakış'], ['ek:rapor', 'Rapor Merkezi', 'chart'], ['ek:onay', 'Onay Bekleyenler', 'user'], ['ek:kurulum', 'Kurulum Durumu', 'gear']]],
    ['Servis', [['/admin/jobs', 'Servis Kayıtları'], ['/admin/appointments', 'Randevular'], ['/admin/quotes', 'Fiyat Teklifleri'], ['/admin/warranty', 'Garanti Talepleri'], ['/admin/customers', 'Müşteriler'], ['ek:m360', 'Müşteri 360', 'user'], ['ek:atolye', 'Atölye (Cihaz Teslim)', 'gear'], ['ek:harita', 'Günün İş Haritası', 'search'], ['/admin/parts', 'Yedek Parça'], ['/admin/diagnosis', 'Arıza Rehberi'], ['/admin/brands', 'Markalar']]],
    ['Ustalar', [['/admin/technicians', 'Teknisyenler'], ['/admin/dealers', 'Bayilik Başvuruları'], ['ek:ustapuan', 'Usta Puanlama', 'user'], ['ek:ustagecmis', 'Usta İş Geçmişi', 'user'], ['/admin/performance', 'Performans'], ['/admin/team', 'Ekip Merkezi'], ['/admin/announcements', 'Duyurular']]],
    ['Muhasebe', [['/admin/accounting', 'Muhasebe'], ['ek:tahsilat', 'Teknisyen Tahsilat', 'cart'], ['ek:cari', 'Cari & Trend', 'cart'], ['ek:vade', 'Usta Borç Vadesi', 'cart'], ['ek:memnun', 'Müşteri Memnuniyeti', 'user'], ['/admin/reports', 'Raporlar']]],
    ['Mağaza & Satış', [['/admin/shop', 'Mağaza'], ['ek:yeni', 'Yeni Sipariş Gir', 'plus'], ['ek:pazar', 'Pazaryerleri', 'cart'], ['ek:urunler', 'Ürün Yönetimi', 'cart'], ['ek:marka', 'Marka Ürün Aktarma', 'cart'], ['/admin/coupons', 'Kuponlar']]],
    ['Web Sitesi', [['/admin/site-features', 'Site Özellikleri'], ['ek:moduller', 'Aç/Kapat & Entegrasyonlar', 'gear'], ['ek:seo', 'SEO · 301 · 404', 'search'], ['/admin/site-studio', 'Site Stüdyosu'], ['/admin/media', 'Medya Kütüphanesi'], ['/admin/integration', 'Site Entegrasyonu']]],
    ['Pazarlama & İletişim', [['/admin/messages', 'İletişim Mesajları'], ['ek:sohbet', 'Canlı Sohbet', 'live'], ['/admin/reviews', 'Yorumlar'], ['ek:gsc', 'Google Search Console', 'search'], ['/admin/marketing', 'Pazarlama Merkezi'], ['ek:canli', 'Canlı Ziyaretçiler', 'search'], ['ek:wa', 'WhatsApp & Bildirim', 'gear'], ['ek:kaynak', 'Kaynak & Arama Analizi', 'search'], ['/admin/growth', 'Büyüme Merkezi'], ['/admin/visitors', 'Ziyaretçiler']]],
    ['Yönetim', [['/admin/settings', 'Ayarlar'], ['ek:yetki', 'Kullanıcılar & Yetkiler', 'user'], ['ek:firmalar', 'Firmalar', 'user'], ['/admin/security', 'Güvenlik'], ['/admin/governance', 'Yedek & Denetim'], ['/admin/account', 'Hesabım']]]
  ];
  var SUB = {
    '/admin/shop': [['orders', 'Siparişler'], ['products', 'Ürünler'], ['bank', 'Havale Bilgileri & Ayarlar']],
    '/admin/site-studio': [['editor', 'Görsel Editör'], ['hero', 'Ana Sayfa Vitrini'], ['theme', 'Renkler & Yazı'], ['global', 'İletişim, Logo & Footer'], ['banner', 'Şerit & Kod'], ['seo', 'SEO'], ['pages', 'Sayfalar'], ['nav', 'Menü & Bağlantılar'], ['bake', 'Statik Yayın']],
    '/admin/marketing': [['ch', 'Kanal Panosu'], ['camp', 'Kampanyalar & Harcama'], ['calls', 'Aramalar'], ['gsc', 'Search Console'], ['pages', 'Sayfalar & İlçe Üretici'], ['audit', 'Site Denetimi'], ['rep', 'Yorumlar & Profil'], ['conn', 'Bağlantılar & Ayarlar']],
    '/admin/visitors': [['overview', 'Genel Bakış'], ['live', 'Canlı'], ['channels', 'Kanal Performansı'], ['content', 'Sayfalar & Kaynaklar'], ['sessions', 'Son Oturumlar']],
    '/admin/team': [['chat', 'Destek Sohbeti'], ['training', 'Eğitim & Sertifika'], ['checklists', 'Kontrol Listeleri'], ['dealers', 'Bayi Portalı']],
    '/admin/accounting': [['overview', 'Genel Bakış'], ['ledger', 'Hareketler & Usta Bakiyeleri'], ['accounts', 'Kasa & Hesaplar'], ['staff', 'Personel'], ['recurring', 'Tekrarlayan & Kategoriler'], ['tax', 'KDV & Fatura'], ['budget', 'Bütçe & Hedef'], ['receivables', 'Alacaklar'], ['import', 'Banka Ekstresi']],
    '/admin/reports': [['general', 'Genel Raporlar'], ['profit', 'İş Bazında Kâr']],
    '/admin/security': [['alerts', 'Güvenlik Uyarıları'], ['logins', 'Giriş Kayıtları'], ['failed', 'Hatalı Girişler'], ['devices', 'Cihazlar'], ['settings', 'Kurallar']],
    '/admin/governance': [['health', 'Sistem Sağlığı'], ['backups', 'Yedekler'], ['audit', 'Denetim Kaydı'], ['trash', 'Çöp Kutusu'], ['notify', 'Bildirim Kanalları']]
  };
  var MPERM = { '/admin': 'dashboard', '/admin/jobs': 'jobs', '/admin/appointments': 'appointments', '/admin/quotes': 'quotes', '/admin/warranty': 'warranty', '/admin/customers': 'customers', '/admin/technicians': 'technicians', '/admin/parts': 'parts', '/admin/shop': 'shop', 'ek:yeni': 'shop', 'ek:atolye': 'jobs', 'ek:ustagecmis': 'technicians', 'ek:tahsilat': 'accounting', 'ek:vade': 'accounting', 'ek:memnun': 'reports', 'ek:rapor': 'reports', 'ek:kurulum': 'settings', 'ek:harita': 'jobs', 'ek:canli': 'visitors', 'ek:wa': 'integration', 'ek:pazar': 'shop', 'ek:marka': 'shop', 'ek:urunler': 'shop', '/admin/coupons': 'coupons', '/admin/site-features': 'site_features', 'ek:moduller': 'site_features', 'ek:seo': 'seo', 'ek:gsc': 'marketing', '/admin/site-studio': 'studio', '/admin/media': 'studio', '/admin/integration': 'integration', '/admin/messages': 'messages', '/admin/reviews': 'reviews', '/admin/dealers': 'dealers', '/admin/marketing': 'marketing', '/admin/growth': 'growth', '/admin/visitors': 'visitors', '/admin/team': 'team', '/admin/performance': 'performance', '/admin/announcements': 'announcements', '/admin/diagnosis': 'diagnosis', '/admin/brands': 'brands', '/admin/accounting': 'accounting', '/admin/reports': 'reports', '/admin/settings': 'settings' };
  var OWNER_ONLY = { 'ek:yetki': 1, 'ek:firmalar': 1, '/admin/security': 1, '/admin/governance': 1, '/admin/users': 1 };
  function me() { try { return JSON.parse(LS.get('user', '{}')) || {}; } catch (e) { return {}; } }
  function canMenu(k) {
    var u = me(), r = u.admin_role || 'owner';
    if (k === '/admin/account') return true;
    if (r === 'owner') return true;
    if (OWNER_ONLY[k]) return false;
    if (r === 'custom') return (u.perms || []).indexOf(MPERM[k]) >= 0;
    if (k.indexOf('ek:') === 0) return r === 'manager' || (r === 'site_editor' && k !== 'ek:yeni' && k !== 'ek:pazar');
    return true; /* eski roller: panelin kendi süzmesi */
  }
  function guardRoute() {
    var u = me(); if (u.admin_role !== 'custom') return; var path = location.pathname.replace(/\/$/, '') || '/'; if (path.indexOf('/admin') !== 0 || path === '/admin/account') return;
    var key = null; Object.keys(MPERM).forEach(function (k) { if (k.indexOf('/') === 0 && (path === k || (k !== '/admin' && path.indexOf(k + '/') === 0))) key = k; });
    if (!key || (u.perms || []).indexOf(MPERM[key]) >= 0) { if (key) return; if (path === '/admin') return; return; }
    var first = null; MENU.forEach(function (g) { g[1].forEach(function (it) { if (!first && it[0].indexOf('/') === 0 && canMenu(it[0])) first = it[0]; }); });
    goto(first || '/admin/account');
  }
  function nativeLinks(nav) { var m = {}; Array.prototype.forEach.call(nav.querySelectorAll(':scope > *:not([data-spx-own]) a[href^="/admin"]'), function (a) { var p = a.getAttribute('href').split('?')[0]; if (!m[p]) m[p] = a; }); return m; }
  function goto(href) { try { history.pushState({}, '', href); window.dispatchEvent(new PopStateEvent('popstate', { state: {} })); } catch (e) { location.href = href; } }
  function closeMobile() { var o = document.querySelector('.fixed.inset-0.z-50 .absolute.inset-0'); if (o) o.click(); }
  function markActive() {
    guardRoute();
    var own = document.querySelector('[data-spx-own]'); if (!own) return; var path = location.pathname.replace(/\/$/, '') || '/', tab = new URLSearchParams(location.search).get('tab');
    var ovOn = ov && ov.classList.contains('on');
    var best = null;
    Array.prototype.forEach.call(own.querySelectorAll('a.spx-it'), function (a) {
      var k = a.getAttribute('data-k'), on = false; if (!k) return;
      if (k.indexOf('ek:') === 0) on = !!ovOn && TAB === k.slice(3); else if (!ovOn) { on = k === '/admin' ? path === '/admin' : (path === k || path.indexOf(k + '/') === 0); }
      a.classList.toggle('on', on); if (on) best = k;
    });
    Array.prototype.forEach.call(own.querySelectorAll('.spx-sub'), function (d) { var k = d.getAttribute('data-for'); d.style.display = (best === k) ? 'block' : 'none'; Array.prototype.forEach.call(d.children, function (a, i) { var t = a.getAttribute('data-t'); a.classList.toggle('on', t === (tab || SUB[k][0][0])); }); });
  }
  var ADMB = null, ADMT = 0, ADMBUSY = false, ADMP = '';
  function ding() { try { if (navigator.vibrate) navigator.vibrate([180, 90, 180]); } catch (e) { } try { var C = window.AudioContext || window.webkitAudioContext; if (!C) return; var c = ding.c || (ding.c = new C()); if (c.state === 'suspended') c.resume(); var o = c.createOscillator(), g = c.createGain(); o.type = 'sine'; o.frequency.value = 880; g.gain.setValueAtTime(0.0001, c.currentTime); g.gain.exponentialRampToValueAtTime(0.25, c.currentTime + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + 0.55); o.connect(g); g.connect(c.destination); o.start(); o.stop(c.currentTime + 0.6); } catch (e) { } }
  function bnotify(t, b) { try { if (window.Notification && Notification.permission === 'granted') new Notification(t, { body: b, icon: '/brand/logo.png' }); } catch (e) { } }
  document.addEventListener('click', function () { try { var C = window.AudioContext || window.webkitAudioContext; if (C && !ding.c) ding.c = new C(); if (window.Notification && Notification.permission === 'default') Notification.requestPermission(); } catch (e) { } }, { once: true });
  function admExtras() {
    var hb = document.querySelector('button[data-testid="open-sidebar"]');
    if (hb && ADMB) { var b = hb.querySelector('.spx-hb'), n = ADMB.total || 0; hb.style.position = 'relative'; if (n > 0) { if (!b) { b = document.createElement('span'); b.className = 'spx-hb'; b.style.cssText = 'position:absolute;top:2px;right:-4px;background:#ef4444;color:#fff;font-size:10px;font-weight:700;border-radius:99px;min-width:16px;height:16px;padding:0 4px;display:flex;align-items:center;justify-content:center;line-height:1'; hb.appendChild(b); } b.textContent = n > 99 ? '99+' : String(n); } else if (b) b.remove(); }
    var mn = document.querySelector('main'), w = document.getElementById('spx-bw'), show = ADMB && ADMB.backup_stale && !/^\/tech/.test(location.pathname) && !(function () { try { return sessionStorage.getItem('spx_bw'); } catch (e) { return ''; } })();
    if (show && mn && !w) { mn.insertAdjacentHTML('afterbegin', '<div id="spx-bw" style="background:#fef2f2;border:1px solid #fca5a5;color:#991b1b;border-radius:10px;padding:10px 12px;margin-bottom:12px;font-size:13px;display:flex;justify-content:space-between;gap:10px"><span><b>⚠ Otomatik yedek uyarısı:</b> son yedek beklenenden eski ya da hiç alınmamış. Yönetim → Yedekler bölümünden kontrol edin.</span><button style="border:0;background:none;font-size:16px;cursor:pointer;color:#991b1b" aria-label="Kapat">×</button></div>'); document.querySelector('#spx-bw button').onclick = function () { try { sessionStorage.setItem('spx_bw', '1'); } catch (e) { } document.getElementById('spx-bw').remove(); }; }
    else if (!show && w) w.remove();
  }
  function admBadges() {
    var u = me(); if (!document.querySelector('[data-spx-own]') || document.body.classList.contains('spx-tech') || (u.role && u.role !== 'admin')) return;
    admExtras();
    var now = Date.now(); if (ADMP !== location.pathname) { ADMP = location.pathname; ADMT = 0; }
    if (!ADMBUSY && now - ADMT > 20000) {
      ADMBUSY = true;
      pcall('GET', '/admin/badges').then(function (r) {
        var o = ADMB; ADMB = r;
        if (o) {
          if (r['/admin/jobs'] > o['/admin/jobs']) { ding(); bnotify('Yeni servis kaydı', (r['/admin/jobs'] - o['/admin/jobs']) + ' yeni kayıt geldi'); }
          else if (r.messages > o.messages) { ding(); bnotify('Yeni mesaj', (r.messages - o.messages) + ' yeni iletişim mesajı'); }
          else if (r['/admin/quotes'] > o['/admin/quotes']) { ding(); bnotify('Yeni fiyat teklifi', 'Bekleyen teklif sayısı: ' + r['/admin/quotes']); }
        }
        try { tick(); tick(); } catch (e) { } admExtras();
      }).catch(function () { }).then(function () { ADMT = Date.now(); ADMBUSY = false; });
    }
  }
  setInterval(admBadges, 1500);
  /* ---------- admin: Servis Kayıtları hızlı filtreleri (Bugün / Gecikmiş / Atanmamış) ---------- */
  var JQ = { k: 'all', map: null, t: 0, busy: false };
  var DONE_ST = { tamamlandi: 1, faturalandi: 1, iptal: 1 };
  function jqMatch(r, k) {
    if (k === 'all') return true;
    var d = new Date(), pad = function (n) { return (n < 10 ? '0' : '') + n; }, day = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()), nowk = day + 'T' + pad(d.getHours()) + ':' + pad(d.getMinutes()), sa = r.sa || '', open = !DONE_ST[r.st];
    if (k === 'today') return sa.slice(0, 10) === day;
    if (k === 'late') return open && !!sa && sa.slice(0, 16) < nowk;
    if (k === 'none') return open && !r.tech;
    if (k === 'nocall') return open && !!r.cd && !r.fc && (r.st === 'atandi' || r.st === 'yolda') && r.cd < new Date().toISOString();
    return true;
  }
  function jobsQuick() {
    var pg = document.querySelector('[data-testid="jobs-page"]'), ex = document.getElementById('spx-jq');
    if (!pg || !/^\/admin\/jobs\/?$/.test(location.pathname)) { if (ex) ex.remove(); JQ.k = 'all'; return; }
    if (!JQ.map && !JQ.busy) { JQ.busy = true; pcall('GET', '/jobs' + jfQs()).then(function (a) { var m = {}; (a || []).forEach(function (x) { m[x.id] = { sa: x.scheduled_at || '', st: x.status, tech: x.assigned_technician_id || '', cd: x.call_due_at || '', fc: x.first_call_at || '', tn: x.assigned_technician_name || '', as: x.assigned_at || '' }; }); JQ.map = m; JQ.t = Date.now(); }).catch(function () { JQ.map = {}; }).then(function () { JQ.busy = false; }); }
    if (JQ.map && !JQ.busy && Date.now() - JQ.t > 30000) { JQ.map = null; }
    if (!ex) {
      var s = document.querySelector('[data-testid="jobs-search"]'), host = s; while (host && host.parentElement !== pg) host = host.parentElement; if (!host) return;
      ex = document.createElement('div'); ex.id = 'spx-jq'; ex.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:-10px 0 4px';
      ex.innerHTML = [['all', 'Tümü'], ['today', '📅 Bugün'], ['late', '⏰ Gecikmiş'], ['none', '👤 Atanmamış'], ['nocall', '📞 Aranmadı']].map(function (c) { return '<button data-q="' + c[0] + '" style="border:1px solid #cbd5e1;background:#fff;color:#0a1f44;border-radius:99px;padding:6px 14px;font-weight:600;font-size:13px;cursor:pointer">' + c[1] + ' <b class="spx-jqn"></b></button>'; }).join('');
      ex.onclick = function (e) { var b = e.target.closest('button[data-q]'); if (!b) return; JQ.k = b.getAttribute('data-q'); jqApply(); };
      host.parentElement.insertBefore(ex, host.nextSibling);
    }
    jqApply();
  }
  function jqApply() {
    var ex = document.getElementById('spx-jq'); if (!ex) return;
    var m = JQ.map || {}, cnt = { today: 0, late: 0, none: 0, nocall: 0 };
    Object.keys(m).forEach(function (id) { ['today', 'late', 'none', 'nocall'].forEach(function (k) { if (jqMatch(m[id], k)) cnt[k]++; }); });
    Array.prototype.forEach.call(ex.querySelectorAll('button[data-q]'), function (b) {
      var k = b.getAttribute('data-q'), on = k === JQ.k; b.style.background = on ? '#0a1f44' : '#fff'; b.style.color = on ? '#fff' : '#0a1f44';
      var n = b.querySelector('.spx-jqn'); n.textContent = k === 'all' ? '' : (JQ.map ? '(' + cnt[k] + ')' : '');
    });
    Array.prototype.forEach.call(document.querySelectorAll('tr[data-testid^="job-row-"]'), function (tr) {
      var id = tr.getAttribute('data-testid').slice(8), r = m[id], hide = JQ.k !== 'all' && JQ.map && r && !jqMatch(r, JQ.k);
      var want = hide ? 'none' : ''; if (tr.style.display !== want) tr.style.display = want;
    });
  }
  setInterval(jobsQuick, 800);

  // ---- GUNCELLEME 108: yeni atanan işte müşteriyi süresinde (15 dk) arama sayacı + admin takibi
  var SLA = { map: null, t: 0, busy: false };
  function slaHM(iso) { var d = new Date(iso); return isNaN(d) ? '' : ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
  function slaMS(ms) { var s = Math.max(0, Math.floor(ms / 1000)), m = Math.floor(s / 60); s = s % 60; return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s; }
  function slaLoad(force) {
    if (SLA.busy || (!force && SLA.map && Date.now() - SLA.t < 20000)) return;
    SLA.busy = true;
    pcall('GET', '/jobs').then(function (a) { var m = {}; (a || []).forEach(function (x) { if (x.call_due_at && (x.status === 'atandi' || x.status === 'yolda')) m[x.id] = { due: x.call_due_at, fc: x.first_call_at || '', n: x.job_number || '', c: x.customer_name || '' }; }); var nt = {}; (a || []).forEach(function (x) { if (x.tech_note && x.status !== 'tamamlandi' && x.status !== 'faturalandi' && x.status !== 'iptal') nt[x.id] = { t: x.tech_note, n: x.job_number || '', c: x.customer_name || '' }; }); SLA.nt = nt; SLA.map = m; SLA.t = Date.now(); }).catch(function () { SLA.map = SLA.map || {}; SLA.t = Date.now(); }).then(function () { SLA.busy = false; });
  }
  function slaPaint(el) {
    var due = Date.parse(el.getAttribute('data-due')), fc = el.getAttribute('data-fc'), left = due - Date.now(), t, bg, fg, adm = el.getAttribute('data-adm');
    var as = Date.parse(el.getAttribute('data-as') || ''), dm = (fc && !isNaN(as)) ? Math.max(0, Math.round((Date.parse(fc) - as) / 60000)) : -1;
    if (fc) { t = '✔ Müşteri arandı · ' + slaHM(fc) + (dm >= 0 ? ' · atamadan ' + dm + ' dk sonra' : ''); bg = '#dcfce7'; fg = '#166534'; }
    else if (adm && left <= 0) { t = '❌ Aranmadı · süre doldu (+' + slaMS(-left) + ')'; bg = '#fee2e2'; fg = '#b91c1c'; }
    else if (adm) { t = '⏳ Aranması bekleniyor · ' + slaMS(left); bg = '#dbeafe'; fg = '#1e3a8a'; }
    else if (left > 0) { t = '📞 Müşteriyi arayın · kalan ' + slaMS(left); if (left < 300000) { bg = '#fef3c7'; fg = '#92400e'; } else { bg = '#dbeafe'; fg = '#1e3a8a'; } }
    else { t = '⏰ Süre doldu — hemen arayın (+' + slaMS(-left) + ')'; bg = '#fee2e2'; fg = '#b91c1c'; }
    if (el.textContent !== t) el.textContent = t;
    if (el.style.background !== bg) { el.style.background = bg; el.style.color = fg; }
  }
  function slaMk(r) { var d = document.createElement('div'); d.className = 'spx-sla'; d.setAttribute('data-due', r.due); d.setAttribute('data-fc', r.fc); d.style.cssText = 'display:inline-block;margin-top:5px;padding:4px 10px;border-radius:99px;font-weight:700;font-size:12.5px;font-variant-numeric:tabular-nums'; slaPaint(d); return d; }
  function slaSync(nm, r) { var nx = nm.nextElementSibling; if (nx && nx.classList.contains('spx-sla')) { if (nx.getAttribute('data-fc') !== r.fc || nx.getAttribute('data-due') !== r.due) { nx.setAttribute('data-fc', r.fc); nx.setAttribute('data-due', r.due); slaPaint(nx); } return; } nm.parentNode.insertBefore(slaMk(r), nm.nextSibling); }
  function slaTech() {
    if (!document.body.classList.contains('spx-tech') || !localStorage.getItem('token')) { return; }
    slaLoad(false); var m = SLA.map; if (!m) return;
    var dm = location.pathname.match(/^\/tech\/jobs\/([^/]+)/);
    Array.prototype.forEach.call(document.querySelectorAll('div.font-display'), function (nm) {
      var tx = (nm.textContent || '').trim(), card = nm.closest('.rounded-xl'); if (!tx || !card || nm.children.length) return;
      var id = null; if (dm) { if (m[dm[1]] && m[dm[1]].c === tx) id = dm[1]; } else { Object.keys(m).forEach(function (k) { if (m[k].c === tx && m[k].n && card.textContent.indexOf(m[k].n) > -1) id = k; }); }
      if (id) slaSync(nm, m[id]);
    });
    Array.prototype.forEach.call(document.querySelectorAll('.spx-sla'), function (e) { if (!e.previousElementSibling) e.remove(); });
  }
  setInterval(slaTech, 700);
  setInterval(function () { Array.prototype.forEach.call(document.querySelectorAll('.spx-sla'), slaPaint); }, 1000);
  document.addEventListener('click', function (e) {
    if (!document.body.classList.contains('spx-tech')) return;
    var a = e.target.closest && e.target.closest('a[href^="tel:"], button'); if (!a) return;
    if (a.tagName === 'BUTTON' && !/^[\d\s()+*\u2022-]{7,}$/.test((a.textContent || '').trim())) return;
    var dm = location.pathname.match(/^\/tech\/jobs\/([^/]+)/), id = dm ? dm[1] : null;
    if (!id && SLA.map) { var card = a.closest('.rounded-xl'); Object.keys(SLA.map).forEach(function (k) { if (card && SLA.map[k].n && card.textContent.indexOf(SLA.map[k].n) > -1) id = k; }); }
    if (!id) return;
    if (SLA.map && SLA.map[id] && !SLA.map[id].fc) SLA.map[id].fc = new Date().toISOString();
    call('POST', '/jobs/' + id + '/call-log', { via: 'tel' }).then(function () { slaLoad(true); }).catch(function () { });
  }, true);
  function slaAdmin() {
    var m = JQ.map; if (!m || !/^\/admin\/jobs\/?$/.test(location.pathname)) return;
    Array.prototype.forEach.call(document.querySelectorAll('tr[data-testid^="job-row-"]'), function (tr) {
      var id = tr.getAttribute('data-testid').slice(8), r = m[id], td = tr.querySelector('td'), ex = tr.querySelector('.spx-sla'); if (!td) return;
      var live = r && r.cd && (r.st === 'atandi' || r.st === 'yolda' || r.fc);
      if (!live) { if (ex) ex.remove(); return; }
      var rr = { due: r.cd, fc: r.fc, as: r.as }; if (!ex) { var d = slaMk(rr); d.setAttribute('data-adm', '1'); d.setAttribute('data-as', rr.as || ''); slaPaint(d); d.style.display = 'block'; d.style.width = 'fit-content'; td.appendChild(d); } else { ex.setAttribute('data-due', rr.due); ex.setAttribute('data-fc', rr.fc); ex.setAttribute('data-as', rr.as || ''); }
    });
  }
  setInterval(slaAdmin, 900);

  // ---- GUNCELLEME 109: telefon alanlari sabit +90 + eksik/yanlis uyarisi (musteri, usta, hizli is)
  function phNorm(v) { var d = String(v || '').replace(/\D/g, ''); if (d.indexOf('00') === 0) d = d.slice(2); if (d.indexOf('90') === 0 && d.length === 12) d = d.slice(2); else if (d.charAt(0) === '0' && d.length === 11) d = d.slice(1); return d; }
  function phOk(d) { var u = {}; d.split('').forEach(function (c) { u[c] = 1; }); return d.length === 10 && '2345'.indexOf(d.charAt(0)) > -1 && Object.keys(u).length >= 3; }
  function phFmt(d) { return d.slice(0, 3) + ' ' + d.slice(3, 6) + ' ' + d.slice(6, 8) + ' ' + d.slice(8); }
  function phSet(inp, v) { try { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(inp, v); inp.dispatchEvent(new Event('input', { bubbles: true })); } catch (e) { } }
  function phInputs() {
    var out = [];
    ['customer-phone-input', 'quick-cust-phone', 'q-customer-phone', 'mj-phone'].forEach(function (t) { var i = document.querySelector('[data-testid="' + t + '"]'); if (i && i.tagName === 'INPUT') out.push([i, t !== 'mj-phone']); });
    var te = document.querySelector('[data-testid="tech-email-input"]');
    if (te) { var dlg = te.closest('[role="dialog"]') || te.closest('form') || document; Array.prototype.forEach.call(dlg.querySelectorAll('input:not([type=password]):not([type=number]):not([type=email])'), function (i) { var lb = i.parentElement && i.parentElement.querySelector('label'); if (lb && /^Telefon/.test((lb.textContent || '').trim())) out.push([i, false]); }); }
    return out;
  }
  function phState(inp, req) { var raw = inp.value || '', d = phNorm(raw); if (!raw.trim()) return req ? 'empty' : 'blank'; return phOk(d) ? 'ok' : 'bad'; }
  function phFix() {
    if (document.body.classList.contains('spx-tech') || !localStorage.getItem('token')) return;
    phInputs().forEach(function (x) {
      var inp = x[0], req = x[1], par = inp.parentElement; if (!par) return;
      if (getComputedStyle(par).position === 'static') par.style.position = 'relative';
      var bd = par.querySelector('.spx-ph90'), wn = par.querySelector('.spx-phwn');
      if (!bd) { bd = document.createElement('span'); bd.className = 'spx-ph90'; bd.textContent = '+90'; bd.style.cssText = 'position:absolute;pointer-events:none;display:flex;align-items:center;padding:0 9px;font-weight:700;font-size:14px;color:#0a1f44;background:#eef2f7;border-right:1px solid #cbd5e1;border-radius:6px 0 0 6px;z-index:2'; par.appendChild(bd); }
      bd.style.left = (inp.offsetLeft + 1) + 'px'; bd.style.top = (inp.offsetTop + 1) + 'px'; bd.style.height = (inp.offsetHeight - 2) + 'px';
      if (inp.style.paddingLeft !== '52px') inp.style.paddingLeft = '52px';
      inp.setAttribute('inputmode', 'tel'); inp.setAttribute('placeholder', '5xx xxx xx xx');
      if (!inp.getAttribute('data-phx')) { inp.setAttribute('data-phx', '1'); inp.addEventListener('blur', function () { var d = phNorm(inp.value); if (phOk(d) && inp.value !== phFmt(d)) phSet(inp, phFmt(d)); }); }
      if (document.activeElement !== inp) { var d0 = phNorm(inp.value); if (phOk(d0) && inp.value !== phFmt(d0)) phSet(inp, phFmt(d0)); }
      if (!wn) { wn = document.createElement('div'); wn.className = 'spx-phwn'; wn.style.cssText = 'font-size:12px;font-weight:600;margin-top:3px'; par.appendChild(wn); }
      var st = phState(inp, req), t = '', c = '#64748b', bc = '';
      if (st === 'bad') { t = '⚠ Numara eksik veya hatalı — +90 sonrası 10 hane yazın (örn. 532 123 45 67)'; c = '#b91c1c'; bc = '#dc2626'; }
      else if (st === 'ok') { t = '✔ +90 ' + phFmt(phNorm(inp.value)); c = '#166534'; }
      else if (st === 'empty') { t = 'Cep telefonu zorunlu — +90 sonrası 10 hane'; }
      if (wn.textContent !== t) { wn.textContent = t; wn.style.color = c; }
      if (inp.style.borderColor !== bc) inp.style.borderColor = bc;
    });
  }
  setInterval(phFix, 600);

  // ---- GUNCELLEME 114: usta profil fotografi (Usta > Profil)
  function avUrl(u) { return u && u.photo_path ? location.origin + '/api/files/' + u.photo_path + '?auth=' + encodeURIComponent(LS.get('token', '')) + '&v=' + encodeURIComponent(u.photo_at || '') : ''; }
  var AV = { u: null, busy: false, t: 0 };
  function avLoad(force) { if (AV.busy || (!force && AV.u && Date.now() - AV.t < 30000)) return; AV.busy = true; pcall('GET', '/auth/me').then(function (u) { AV.u = u; AV.t = Date.now(); }).catch(function () { AV.u = AV.u || {}; AV.t = Date.now(); }).then(function () { AV.busy = false; }); }
  function avShrink(file) {
    return new Promise(function (ok, no) {
      var img = new Image(), url = URL.createObjectURL(file);
      img.onload = function () { var S = 480, w = img.naturalWidth, h = img.naturalHeight, m = Math.min(w, h), c = document.createElement('canvas'); c.width = c.height = S; c.getContext('2d').drawImage(img, (w - m) / 2, (h - m) / 2, m, m, 0, 0, S, S); URL.revokeObjectURL(url); c.toBlob(function (b) { b ? ok(b) : no(new Error('Fotoğraf okunamadı')); }, 'image/jpeg', 0.82); };
      img.onerror = function () { URL.revokeObjectURL(url); no(new Error('Bu dosya fotoğraf olarak açılamadı')); };
      img.src = url;
    });
  }
  function avPaint(box) {
    var u = AV.u || {}, src = avUrl(u), nm = (u.name || '?').trim(), ini = nm.split(/\s+/).slice(0, 2).map(function (x) { return x.charAt(0).toUpperCase(); }).join('');
    var sig = (u.photo_path || '') + '|' + (u.photo_at || '') + '|' + nm; if (box.getAttribute('data-sig') === sig) return; box.setAttribute('data-sig', sig);
    box.querySelector('.spx-avc').innerHTML = src ? '<img src="' + src + '" alt="" style="width:100%;height:100%;object-fit:cover;display:block">' : '<span style="font-weight:800;font-size:30px;color:#fff">' + esc(ini) + '</span>';
    box.querySelector('[data-a=del]').style.display = src ? '' : 'none';
    box.querySelector('[data-a=add]').textContent = src ? '📷 Fotoğrafı değiştir' + (u.photo_status === 'pending' ? ' (onay bekliyor)' : '') : '📷 Fotoğraf ekle';
  }
  function avTech() {
    var pg = document.querySelector('[data-testid="tech-profile"]'), ex = document.getElementById('spx-av');
    if (!pg || !document.body.classList.contains('spx-tech')) { if (ex) ex.remove(); return; }
    avLoad(false); if (!AV.u) return;
    if (!ex) {
      ex = document.createElement('div'); ex.id = 'spx-av'; ex.className = 'notranslate rounded-xl border bg-card p-4 shadow-none border-slate-200'; ex.style.cssText = 'display:flex;gap:14px;align-items:center;margin-bottom:12px';
      ex.innerHTML = '<div class="spx-avc" style="width:84px;height:84px;border-radius:50%;background:#0a1f44;overflow:hidden;display:flex;align-items:center;justify-content:center;flex:none;border:3px solid #e2e8f0"></div><div style="flex:1;min-width:0"><div style="font-weight:700;font-size:14px;margin-bottom:2px">Profil fotoğrafı</div><div style="font-size:12px;color:#64748b;margin-bottom:8px">İsteğe bağlı. Yönetim ve müşteri iletişiminde tanınmanız için net bir yüz fotoğrafı ekleyebilirsiniz.</div><div style="display:flex;gap:8px;flex-wrap:wrap"><button type="button" data-a="add" style="border:0;background:#2563eb;color:#fff;border-radius:10px;padding:9px 13px;font-weight:700;font-size:13px"></button><button type="button" data-a="del" style="border:1px solid #cbd5e1;background:#fff;color:#b91c1c;border-radius:10px;padding:9px 13px;font-weight:700;font-size:13px">Kaldır</button></div><input type="file" accept="image/*" style="display:none"></div>';
      var fi = ex.querySelector('input[type=file]');
      ex.onclick = function (e) {
        var a = e.target.getAttribute && e.target.getAttribute('data-a'); if (!a) return;
        if (a === 'add') fi.click();
        else if (a === 'del') { if (!confirm('Profil fotoğrafı kaldırılsın mı?')) return; call('DELETE', '/tech/photo').then(function () { toast('Fotoğraf kaldırıldı'); avLoad(true); AV.u.photo_path = ''; ex.removeAttribute('data-sig'); avPaint(ex); }).catch(fail); }
      };
      fi.onchange = function () {
        var f = fi.files && fi.files[0]; fi.value = ''; if (!f) return; toast('Fotoğraf yükleniyor…');
        avShrink(f).then(function (blob) {
          var fd = new FormData(); fd.append('file', blob, 'profil.jpg');
          return fetch(API + '/upload', { method: 'POST', headers: { Authorization: 'Bearer ' + LS.get('token', '') }, body: fd }).then(function (r) { return r.json().then(function (j) { if (!r.ok) throw new Error(j.detail || 'Yükleme başarısız'); return j; }); });
        }).then(function (j) { return call('POST', '/tech/photo', { path: j.path }); }).then(function (j) { AV.u.photo_path = j.photo_path; AV.u.photo_at = new Date().toISOString(); ex.removeAttribute('data-sig'); avPaint(ex); toast('Fotoğrafınız kaydedildi ✔ — yönetim onayından sonra müşteriye görünür'); avLoad(true); }).catch(fail);
      };
      pg.insertBefore(ex, pg.firstChild);
    }
    avPaint(ex);
  }
  setInterval(avTech, 800);

  // ---- GUNCELLEME 118: usta profilinde iletisim/konum duzenleme + musteri yorumlari
  var UC = { loaded: false, busy: false };
  function ucCard() {
    var pg = document.querySelector('[data-testid="tech-profile"]'), ex = document.getElementById('spx-uc');
    if (!pg || !document.body.classList.contains('spx-tech')) { if (ex) ex.remove(); UC.loaded = false; return; }
    if (ex) return;
    var inp = 'width:100%;border:1px solid #cbd5e1;border-radius:10px;padding:10px 12px;font-size:15px;background:#fff;color:#0f172a;box-sizing:border-box', lb = 'display:block;font-size:12px;font-weight:700;color:#475569;margin:10px 0 4px';
    ex = document.createElement('div'); ex.id = 'spx-uc'; ex.className = 'notranslate rounded-xl border bg-card p-4 shadow-none border-slate-200'; ex.style.cssText = 'margin-bottom:12px';
    ex.innerHTML = '<div style="font-weight:700;font-size:14px">İletişim ve konum bilgilerim</div><div style="font-size:12px;color:#64748b;margin-top:2px">Bilgileriniz yönetimde görünür. İstediğiniz zaman değiştirebilirsiniz.</div>' +
      '<label style="' + lb + '">E-posta (giriş adresiniz)</label><input data-f="email" type="email" autocomplete="email" style="' + inp + '">' +
      '<label style="' + lb + '">Telefon</label><div style="display:flex;align-items:stretch"><span style="display:flex;align-items:center;padding:0 10px;font-weight:700;color:#0a1f44;background:#f1f5f9;border:1px solid #cbd5e1;border-right:0;border-radius:10px 0 0 10px">+90</span><input data-f="phone" inputmode="tel" placeholder="5xx xxx xx xx" style="' + inp + ';border-radius:0 10px 10px 0"></div><div data-w="phone" style="font-size:12px;font-weight:600;margin-top:3px"></div>' +
      '<label style="' + lb + '">İl</label><input data-f="city" placeholder="Örn: Ankara" style="' + inp + '">' +
      '<label style="' + lb + '">Hizmet verdiğiniz ilçeler</label><input data-f="districts" placeholder="Örn: Etimesgut, Çankaya, Keçiören" style="' + inp + '">' +
      '<label style="' + lb + '">Adres / konum</label><textarea data-f="address" rows="2" maxlength="300" placeholder="Mahalle, cadde, ilçe/il" style="' + inp + ';resize:vertical"></textarea>' +
      '<div style="display:flex;gap:8px;align-items:center;margin-top:12px"><button data-a="save" style="border:0;background:#0a1f44;color:#fff;border-radius:10px;padding:10px 16px;font-weight:700;font-size:14px">Kaydet</button><span data-w="msg" style="font-size:12.5px;font-weight:600"></span></div>';
    pg.insertBefore(ex, pg.children[1] || null);
    var F = function (n) { return ex.querySelector('[data-f=' + n + ']'); }, W = function (n) { return ex.querySelector('[data-w=' + n + ']'); };
    pcall('GET', '/tech/contact').then(function (c) { c = c || {}; F('email').value = c.email || ''; var d = phNorm(c.phone || ''); F('phone').value = phOk(d) ? phFmt(d) : (c.phone || ''); F('city').value = c.city || ''; F('districts').value = c.districts || ''; F('address').value = c.address || ''; UC.loaded = true; }).catch(function () { W('msg').textContent = 'Bilgiler yüklenemedi'; W('msg').style.color = '#b91c1c'; });
    F('phone').addEventListener('input', function () { var d = phNorm(F('phone').value), w = W('phone'); if (!F('phone').value.trim()) { w.textContent = 'Telefon zorunlu'; w.style.color = '#b91c1c'; } else if (phOk(d)) { w.textContent = '✔ +90 ' + phFmt(d); w.style.color = '#166534'; } else { w.textContent = 'Eksik veya hatalı numara'; w.style.color = '#b91c1c'; } });
    ex.onclick = function (e) {
      if (!e.target.getAttribute || e.target.getAttribute('data-a') !== 'save') return;
      if (!UC.loaded) { toast('Bilgiler yükleniyor, birazdan tekrar deneyin'); return; }
      var d = phNorm(F('phone').value), m = W('msg'); if (!phOk(d)) { m.textContent = 'Telefon numarası eksik veya hatalı'; m.style.color = '#b91c1c'; return; }
      var em = F('email').value.trim(); if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(em)) { m.textContent = 'E-posta geçersiz'; m.style.color = '#b91c1c'; return; }
      m.textContent = 'Kaydediliyor…'; m.style.color = '#64748b';
      call('PUT', '/tech/contact', { email: em, phone: '+90' + d, city: F('city').value, districts: F('districts').value, address: F('address').value }).then(function (r) { m.textContent = '✔ Kaydedildi'; m.style.color = '#166534'; F('email').value = r.email; F('phone').value = phFmt(phNorm(r.phone)); toast('Bilgileriniz kaydedildi ✔'); avLoad(true); setTimeout(function () { location.reload(); }, 900); }).catch(function (er) { m.textContent = (er && er.message) || 'Kaydedilemedi'; m.style.color = '#b91c1c'; });
    };
  }
  setInterval(ucCard, 900);

  var RV = { d: null, t: 0, busy: false, n: 15 };
  function rvLoad() { if (RV.busy || (RV.d && Date.now() - RV.t < 60000)) return; RV.busy = true; pcall('GET', '/tech/reviews').then(function (d) { RV.d = d; RV.t = Date.now(); }).catch(function () { RV.d = RV.d || { count: 0, avg: 0, dist: {}, items: [] }; RV.t = Date.now(); }).then(function () { RV.busy = false; }); }
  function rvStars(n) { return '<span style="color:#f59e0b;letter-spacing:1px">' + '★★★★★'.slice(0, n) + '</span><span style="color:#cbd5e1;letter-spacing:1px">' + '★★★★★'.slice(n) + '</span>'; }
  function rvHtml(d) {
    var h = '<div style="font-weight:700;font-size:14px;margin-bottom:8px">⭐ Müşteri yorumlarım</div>';
    if (!d.count) return h + '<div style="font-size:13px;color:#64748b">Henüz değerlendirme yok. Tamamladığınız işlerde müşteriler puan ve yorum bıraktığında burada görünür.</div>';
    h += '<div style="display:flex;gap:14px;align-items:center;margin-bottom:10px"><div style="font-size:34px;font-weight:800;color:#0a1f44;line-height:1">' + String(d.avg).replace('.', ',') + '</div><div>' + rvStars(Math.round(d.avg)) + '<div style="font-size:12px;color:#64748b">' + d.count + ' değerlendirme</div></div>' +
      '<div style="flex:1;font-size:11px;color:#64748b">' + [5, 4, 3, 2, 1].map(function (k) { var c = (d.dist || {})[k] || 0, w = Math.round(c * 100 / d.count); return '<div style="display:flex;align-items:center;gap:5px"><span style="width:8px">' + k + '</span><div style="flex:1;height:5px;background:#e2e8f0;border-radius:3px"><div style="width:' + w + '%;height:5px;background:#f59e0b;border-radius:3px"></div></div><span style="width:18px;text-align:right">' + c + '</span></div>'; }).join('') + '</div></div>';
    var it = d.items || [];
    it.slice(0, RV.n).forEach(function (r) { h += '<div style="border-top:1px solid #e2e8f0;padding:9px 0"><div style="display:flex;justify-content:space-between;gap:8px;font-size:12.5px"><b>' + esc(r.name) + '</b><span style="color:#94a3b8">' + esc((r.at || '').slice(0, 10).split('-').reverse().join('.')) + '</span></div><div style="font-size:14px">' + rvStars(r.rating) + ' <span style="font-size:11.5px;color:#94a3b8">' + esc(r.job_number) + (r.device ? ' · ' + esc(r.device) : '') + '</span></div>' + (r.comment ? '<div style="font-size:14px;margin-top:3px;color:#0f172a;white-space:pre-wrap">' + esc(r.comment) + '</div>' : '<div style="font-size:12.5px;color:#94a3b8;margin-top:3px">' + (r.comment_pending ? 'Yorum, yönetim onayından sonra görünür' : 'Yorum yazılmadı') + '</div>') + '</div>'; });
    if (it.length > RV.n) h += '<button data-a="more" style="border:1px solid #cbd5e1;background:#fff;border-radius:10px;padding:8px 14px;font-weight:700;font-size:13px;margin-top:6px">Daha fazla göster</button>';
    return h;
  }
  function rvCard() {
    var ex = document.getElementById('spx-rv'), pg = document.querySelector('[data-testid="tech-profile"]'), more = location.pathname.replace(/\/$/, '') === '/tech/more', host = pg || (more ? document.querySelector('main') : null);
    if (!document.body.classList.contains('spx-tech') || !host) { if (ex) ex.remove(); return; }
    rvLoad(); if (!RV.d) return;
    if (ex && ex.parentNode !== host) { ex.remove(); ex = null; }
    if (!ex) { ex = document.createElement('div'); ex.id = 'spx-rv'; ex.className = 'notranslate rounded-xl border bg-card p-4 shadow-none border-slate-200'; ex.style.cssText = pg ? 'margin-bottom:12px' : 'margin:12px 0;background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:14px'; ex.onclick = function (e) { if (e.target.getAttribute && e.target.getAttribute('data-a') === 'more') { RV.n += 20; ex.removeAttribute('data-sig'); } }; if (pg) pg.insertBefore(ex, pg.children[2] || null); else host.appendChild(ex); }
    var sig = RV.t + '|' + RV.n; if (ex.getAttribute('data-sig') !== sig) { ex.setAttribute('data-sig', sig); ex.innerHTML = rvHtml(RV.d); }
  }
  setInterval(rvCard, 1000);

  // ---- GUNCELLEME 122: Hizmet Puani (5 uzerinden: yorum + ise gitme + arama + bitirme hizi)
  var SC = { d: null, t: 0, busy: false };
  function scLoad() { if (SC.busy || (SC.d && Date.now() - SC.t < 60000)) return; SC.busy = true; pcall('GET', '/tech/score').then(function (d) { SC.d = d; SC.t = Date.now(); }).catch(function () { SC.t = Date.now(); }).then(function () { SC.busy = false; }); }
  var SC_HELP = '<details style="margin-top:8px"><summary style="font-size:12.5px;font-weight:700;color:#2563eb;cursor:pointer">Puan nasıl hesaplanır?</summary><div style="font-size:12.5px;line-height:1.6;color:#334155;margin-top:6px">Son 180 günde tamamladığınız işlerin dört ölçütü 5 üzerinden puanlanır ve ağırlıklı ortalaması alınır. En az 3 tamamlanmış işten sonra puanınız görünür.<br>' +
    '<b>Müşteri yorumları (%35):</b> müşterinin verdiği 1–5 puan.<br><b>İşe gitme hızı (%25):</b> randevu saatinden (yoksa atamadan) yola çıkma/işe başlama: 60 dk içinde 5 · 120 dk 4 · 240 dk 3 · 480 dk 2 · daha geç 1.<br><b>Müşteriyi arama hızı (%20):</b> atamadan ilk aramaya: 15 dk içinde 5 · 30 dk 4 · 60 dk 3 · 120 dk 2 · daha geç/aranmadı 1.<br><b>İşi bitirme hızı (%20):</b> başlamadan tamamlamaya: 2 saat içinde 5 · 4 saat 4 · 8 saat 3 · 24 saat 2 · daha uzun 1 (atölye işleri hariç).<br>' +
    'Puan 3,5 altına inerse yönetim sizinle görüşür; 3,0 altında iş yönlendirmesi azalabilir; 2,5 altında atama geçici durdurulabilir. İtirazınızı 7 gün içinde yönetime bildirebilirsiniz.</div></details>';
  function scHtml(d) {
    var h = '<div style="font-weight:700;font-size:14px;margin-bottom:8px">🏅 Hizmet puanım</div>';
    var P = d.parts || {}, ord = ['review', 'go', 'call', 'finish'];
    if (!d.has) h += '<div style="font-size:13px;color:#64748b;margin-bottom:8px">Puanınız en az ' + (d.min_jobs || 3) + ' tamamlanmış işten sonra görünür (şu an ' + (d.jobs || 0) + ' iş).</div>';
    else h += '<div style="display:flex;gap:12px;align-items:center;margin-bottom:8px"><div style="font-size:36px;font-weight:800;color:#0a1f44;line-height:1">' + String(d.score.toFixed(1)).replace('.', ',') + '<span style="font-size:15px;color:#64748b;font-weight:700"> / 5</span></div><div style="font-size:12px;color:#64748b">Son ' + d.days + ' gün · ' + d.jobs + ' tamamlanan iş</div></div>';
    ord.forEach(function (k) { var p = P[k]; if (!p) return; var v = p.avg, w = v ? Math.round(v * 20) : 0; h += '<div style="margin:7px 0"><div style="display:flex;justify-content:space-between;font-size:12.5px"><span>' + esc(p.label) + ' <span style="color:#94a3b8">· %' + p.weight + '</span></span><b>' + (v ? String(v.toFixed(1)).replace('.', ',') : '—') + '</b></div><div style="height:6px;background:#e2e8f0;border-radius:3px"><div style="width:' + w + '%;height:6px;background:' + (v >= 4 ? '#16a34a' : v >= 3 ? '#f59e0b' : '#dc2626') + ';border-radius:3px"></div></div></div>'; });
    return h + SC_HELP;
  }
  function scCard() {
    var ex = document.getElementById('spx-sc'), pg = document.querySelector('[data-testid="tech-profile"]'), more = location.pathname.replace(/\/$/, '') === '/tech/more', host = pg || (more ? document.querySelector('main') : null);
    if (!document.body.classList.contains('spx-tech') || !host) { if (ex) ex.remove(); return; }
    scLoad(); if (!SC.d) return;
    if (ex && ex.parentNode !== host) { ex.remove(); ex = null; }
    if (!ex) { ex = document.createElement('div'); ex.id = 'spx-sc'; ex.className = 'notranslate rounded-xl border bg-card p-4 shadow-none border-slate-200'; ex.style.cssText = pg ? 'margin-bottom:12px' : 'margin:12px 0;background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:14px'; if (pg) pg.insertBefore(ex, pg.children[2] || null); else host.appendChild(ex); }
    var sig = String(SC.t); if (ex.getAttribute('data-sig') !== sig) { var op = ex.querySelector('details') && ex.querySelector('details').open; ex.setAttribute('data-sig', sig); ex.innerHTML = scHtml(SC.d); if (op) ex.querySelector('details').open = true; }
  }
  setInterval(scCard, 1000);
  function adminScoreCard() {
    if (TAB !== 'ustapuan') return;
    pcall('GET', '/admin/tech-scores?days=180').then(function (d) {
      var b = body(); if (!b || TAB !== 'ustapuan' || document.getElementById('spx-adsc')) return;
      var c = document.createElement('div'); c.id = 'spx-adsc'; c.className = 'spx-card';
      var f = function (p) { return p && p.avg ? String(p.avg.toFixed(1)).replace('.', ',') + ' <small style="color:#94a3b8">(' + p.n + ')</small>' : '—'; };
      c.innerHTML = '<b>ServisPlus Hizmet Puanı (5 üzerinden, son 180 gün)</b><small style="color:#64748b;display:block;margin:4px 0 8px">Yorum %35 · İşe gitme %25 · Müşteriyi arama %20 · İşi bitirme %20. Ustanın profilinde ve sertifikasında görünen puan budur. 3 işten azı “Yeni”dir.</small>' +
        tbl(['Usta', 'Puan', 'Yorum', 'İşe gitme', 'Arama', 'Bitirme', 'İş'], d.rows.map(function (r) { var P = r.parts || {}; return tr_(['<b>' + esc(r.name) + '</b>' + (r.active ? '' : ' <small>(pasif)</small>'), r.has ? '<b style="font-size:15px">' + String(r.score.toFixed(1)).replace('.', ',') + '</b>' : '<small>Yeni</small>', f(P.review), f(P.go), f(P.call), f(P.finish), r.jobs]); }));
      b.appendChild(c);
    }).catch(function () { });
  }
  setInterval(function () { if (TAB === 'ustapuan' && body() && body().querySelector('table') && !document.getElementById('spx-adsc')) adminScoreCard(); }, 1500);

  // ---- GUNCELLEME 119: usta "Sertifikalar" (Hizmet Veren Belgesi + Uye Etiketi) - Daha sayfasi, PDF olarak kaydet
  var CE = { d: null, busy: false, t: 0, logo: '' };
  (function () { try { var sc = document.createElement('script'); sc.src = '/belge.js?v=1'; document.head.appendChild(sc); if (!window.qrcode) { var sq = document.createElement('script'); sq.src = 'https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js'; document.head.appendChild(sq); } } catch (e) { } try { fetch('/logo-servisplus.jpg').then(function (r) { return r.ok ? r.blob() : null; }).then(function (b) { if (!b) return; var fr = new FileReader(); fr.onload = function () { CE.logo = fr.result; }; fr.readAsDataURL(b); }).catch(function () { }); } catch (e) { } })();
  function ceLoad() { if (CE.busy || (CE.d && Date.now() - CE.t < 120000)) return; CE.busy = true; pcall('GET', '/tech/certificate?base=' + encodeURIComponent(location.origin)).then(function (d) { CE.d = d; CE.t = Date.now(); }).catch(function () { CE.t = Date.now(); }).then(function () { CE.busy = false; }); }
  function ceHtml(kind, d) { return window.spBelge ? window.spBelge.html(kind, d, CE.logo) : ''; }
  function ceOpen(kind) {
    var d = CE.d; if (!d || !d.name) { toast('Bilgiler yükleniyor, birazdan tekrar deneyin'); return; }
    var old = document.getElementById('spx-cev'); if (old) old.remove();
    var ov = document.createElement('div'); ov.id = 'spx-cev'; ov.className = 'notranslate'; ov.style.cssText = 'position:fixed;inset:0;z-index:99998;background:#0f172a;display:flex;flex-direction:column';
    var html = ceHtml(kind, d);
    ov.innerHTML = '<div style="display:flex;gap:8px;align-items:center;padding:10px 12px;background:#fff"><button data-a="x" style="border:1px solid #cbd5e1;background:#fff;border-radius:10px;padding:9px 14px;font-weight:700;font-size:14px">← Geri</button><div style="flex:1;font-weight:700;font-size:14px;text-align:center">' + (kind === 'etiket' ? 'Üye Etiketi' : 'Hizmet Veren Belgesi') + '</div><button data-a="pdf" style="border:0;background:#2563eb;color:#fff;border-radius:10px;padding:9px 14px;font-weight:700;font-size:14px">PDF kaydet</button></div><div style="flex:1;overflow:auto;padding:12px;display:flex;justify-content:center"><div id="spx-cef" style="width:100%;max-width:520px"></div></div>';
    document.body.appendChild(ov);
    var fr = document.createElement('iframe'); fr.style.cssText = 'border:0;background:#fff;width:210mm;height:297mm;transform-origin:0 0;box-shadow:0 8px 30px rgba(0,0,0,.4)'; fr.srcdoc = html; var host = ov.querySelector('#spx-cef'); host.style.position = 'relative'; host.appendChild(fr);
    function fit() { var w = host.clientWidth, k = w / (210 * 3.7795); fr.style.transform = 'scale(' + k + ')'; host.style.height = (297 * 3.7795 * k) + 'px'; }
    fit(); setTimeout(fit, 50);
    ov.onclick = function (e) {
      var a = e.target.getAttribute && e.target.getAttribute('data-a'); if (!a) return;
      if (a === 'x') ov.remove();
      if (a === 'pdf') { var w = window.open('', '_blank'); if (!w) { try { fr.contentWindow.focus(); fr.contentWindow.print(); } catch (er) { toast('Açılır pencereye izin verin'); } return; } w.document.open(); w.document.write(html.replace('</body>', '<script>window.onload=function(){setTimeout(function(){window.print()},500)}<\/script></body>')); w.document.close(); }
    };
  }
  function ceTile(kind, ttl, sub, prev) { return '<div data-k="' + kind + '" style="display:flex;gap:12px;align-items:center;border:1px solid #e2e8f0;border-radius:14px;padding:10px;margin-top:10px;background:#fff;cursor:pointer"><div style="width:64px;height:90px;flex:none;border-radius:8px;overflow:hidden;position:relative;background:' + prev + '"></div><div style="flex:1;min-width:0"><div style="font-weight:700;font-size:14px">' + ttl + '</div><div style="font-size:12px;color:#64748b;margin-top:2px">' + sub + '</div><div style="margin-top:7px"><span style="display:inline-block;background:#0a1f44;color:#fff;border-radius:8px;padding:6px 12px;font-size:12.5px;font-weight:700">Aç / PDF kaydet</span></div></div></div>'; }
  function ceCard() {
    var ex = document.getElementById('spx-ce'), more = location.pathname.replace(/\/$/, '') === '/tech/more', m = document.querySelector('main');
    if (!document.body.classList.contains('spx-tech') || !more || !m) { if (ex) ex.remove(); return; }
    ceLoad(); if (ex) return;
    ex = document.createElement('div'); ex.id = 'spx-ce'; ex.className = 'notranslate'; ex.style.cssText = 'margin:12px 0;background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:14px';
    ex.innerHTML = '<div style="font-weight:800;font-size:15px">📜 Sertifikalar</div><div style="font-size:12.5px;color:#64748b;margin-top:2px">Müşteri sorarsa gösterebileceğiniz, adınıza hazırlanmış belgeler. PDF olarak kaydedip yazdırabilirsiniz.</div>' +
      ceTile('belge', 'Hizmet Veren Belgesi', 'A4 · masa üstü veya çerçeve için', 'linear-gradient(160deg,#14408f,#0a1f44)') + ceTile('etiket', 'ServisPlus İş Ortağı Etiketi', 'Yuvarlak etiket · araç / vitrin için', 'radial-gradient(circle at 50% 50%,#14408f,#0a1f44)');
    ex.onclick = function (e) { var t = e.target.closest && e.target.closest('[data-k]'); if (t) ceOpen(t.getAttribute('data-k')); };
    m.appendChild(ex);
  }
  setInterval(ceCard, 1000);

  // ---- GUNCELLEME 115: admin servis kaydi detayinda "musteri ne zaman / kac dk sonra arandi" karti
  var JC = { id: '', j: null, t: 0, busy: false };
  function jobCallCard() {
    var pg = document.querySelector('[data-testid="job-detail-page"]'), ex = document.getElementById('spx-jc'), m = location.pathname.match(/^\/admin\/jobs\/([^/]+)/);
    if (!pg || !m) { if (ex) ex.remove(); JC.id = ''; return; }
    if (JC.id !== m[1]) { JC.id = m[1]; JC.j = null; JC.t = 0; if (ex) ex.remove(); ex = null; }
    if ((!JC.j || Date.now() - JC.t > 15000) && !JC.busy) { JC.busy = true; pcall('GET', '/jobs/' + m[1]).then(function (j) { JC.j = j; JC.t = Date.now(); }).catch(function () { JC.t = Date.now(); }).then(function () { JC.busy = false; }); }
    var j = JC.j; if (!j || !j.assigned_at) { if (ex) ex.remove(); return; }
    var host = document.querySelector('[data-testid="status-select"]'); host = host && host.closest('.rounded-xl'); if (!host) return;
    var as = Date.parse(j.assigned_at), due = Date.parse(j.call_due_at), fc = j.first_call_at ? Date.parse(j.first_call_at) : 0, lim = Math.round((due - as) / 60000);
    var calls = (j.calls || []).map(function (c) { return slaHM(c.at) + (c.by ? ' (' + esc(c.by) + ')' : ''); });
    var h;
    if (fc) { var dm = Math.max(0, Math.round((fc - as) / 60000)), late = dm - lim; h = '<b style="color:' + (late > 0 ? '#b91c1c' : '#166534') + '">' + (late > 0 ? '⚠ Müşteri geç arandı' : '✔ Müşteri süresinde arandı') + '</b><div style="font-size:13px;margin-top:3px">Atanma: <b>' + slaHM(j.assigned_at) + '</b> · İlk arama: <b>' + slaHM(j.first_call_at) + '</b> · <b>atamadan ' + dm + ' dk sonra</b>' + (late > 0 ? ' (süre ' + lim + ' dk, +' + late + ' dk gecikme)' : '') + '</div>' + (j.call_by ? '<div style="font-size:12.5px;color:#475569;margin-top:2px">Arayan: ' + esc(j.call_by) + '</div>' : '') + (calls.length > 1 ? '<div style="font-size:12.5px;color:#475569;margin-top:2px">Tüm arama kayıtları: ' + calls.join(', ') + '</div>' : ''); }
    else { var open = j.status === 'atandi' || j.status === 'yolda', left = due - Date.now(); h = open ? (left > 0 ? '<b style="color:#1e3a8a">⏳ Müşterinin aranması bekleniyor</b><div style="font-size:13px;margin-top:3px">Atanma: <b>' + slaHM(j.assigned_at) + '</b> · kalan süre: <b>' + slaMS(left) + '</b> (süre ' + lim + ' dk)</div>' : '<b style="color:#b91c1c">❌ Müşteri aranmadı — süre doldu</b><div style="font-size:13px;margin-top:3px">Atanma: <b>' + slaHM(j.assigned_at) + '</b> · ' + lim + ' dk doldu, <b>+' + slaMS(-left) + '</b> geçti</div>') : '<b style="color:#64748b">Arama kaydı yok</b><div style="font-size:13px;margin-top:3px">Atanma: <b>' + slaHM(j.assigned_at) + '</b> · usta arama düğmesine basmadan iş ilerledi.</div>'; }
    h += '<div style="font-size:11.5px;color:#94a3b8;margin-top:5px">Arama düğmesine basma zamanı kaydedilir; görüşmenin süresi ölçülmez.</div>';
    var bg = fc ? (fc - as > (due - as) ? '#fef2f2' : '#f0fdf4') : ((j.status === 'atandi' || j.status === 'yolda') && due < Date.now() ? '#fef2f2' : '#eff6ff');
    if (!ex) { ex = document.createElement('div'); ex.id = 'spx-jc'; ex.className = 'notranslate'; ex.style.cssText = 'border:1px solid #e2e8f0;border-radius:12px;padding:11px 13px;margin-bottom:14px;font-size:14px'; host.insertBefore(ex, host.firstChild); }
    if (ex.getAttribute('data-h') !== h) { ex.setAttribute('data-h', h); ex.innerHTML = '<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:#64748b;font-weight:700;margin-bottom:4px">📞 Müşteri arama takibi</div>' + h; }
    ex.style.background = bg;
  }
  setInterval(jobCallCard, 1000);

  // ---- GUNCELLEME 116: "Ustaya ozel not" - admin yazar, usta gorur; musteri/PDF/takip sayfasinda GORUNMEZ
  var TN = { id: '', dirty: false };
  function tnCard() {
    var pg = document.querySelector('[data-testid="job-detail-page"]'), ex = document.getElementById('spx-tn'), m = location.pathname.match(/^\/admin\/jobs\/([^/]+)/);
    if (!pg || !m || !JC.j || JC.j.id !== m[1]) { if (ex && (!pg || !m)) ex.remove(); return; }
    var host = document.querySelector('[data-testid="status-select"]'); host = host && host.closest('.rounded-xl'); if (!host) return;
    if (TN.id !== m[1]) { TN.id = m[1]; TN.dirty = false; if (ex) { ex.remove(); ex = null; } }
    if (!ex) {
      ex = document.createElement('div'); ex.id = 'spx-tn'; ex.className = 'notranslate'; ex.style.cssText = 'border:1px solid #fcd34d;background:#fffbeb;border-radius:12px;padding:11px 13px;margin-bottom:14px';
      ex.innerHTML = '<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:#92400e;font-weight:800;margin-bottom:2px">🔒 Ustaya özel not</div><div style="font-size:12px;color:#92400e;margin-bottom:6px">Bu notu yalnızca atanan usta görür. Müşteri, servis formu (PDF) ve takip sayfasında görünmez.</div>' +
        '<textarea maxlength="1000" rows="3" placeholder="Örn: Müşteri yaşlı, kapıyı geç açabilir. Önce arayın. Daha önce aynı arıza için geldi." style="width:100%;border:1px solid #fcd34d;border-radius:8px;padding:8px 10px;font-size:14px;background:#fff;resize:vertical"></textarea>' +
        '<div style="display:flex;gap:8px;align-items:center;margin-top:6px"><button type="button" style="border:0;background:#b45309;color:#fff;border-radius:8px;padding:8px 14px;font-weight:700;font-size:13px">Notu kaydet</button><span class="spx-tns" style="font-size:12px;color:#64748b"></span></div>';
      var ta = ex.querySelector('textarea'), bt = ex.querySelector('button'), st = ex.querySelector('.spx-tns');
      ta.value = JC.j.tech_note || ''; if (JC.j.tech_note_at) st.textContent = 'Son kayıt: ' + slaHM(JC.j.tech_note_at) + (JC.j.tech_note_by ? ' · ' + JC.j.tech_note_by : '');
      ta.oninput = function () { TN.dirty = true; st.textContent = 'Kaydedilmedi'; };
      bt.onclick = function () { bt.disabled = true; call('PUT', '/jobs/' + m[1], { tech_note: ta.value }).then(function (j) { TN.dirty = false; JC.j = j && j.id ? j : JC.j; if (JC.j) JC.j.tech_note = ta.value; st.textContent = 'Kaydedildi ✔ — usta görebilir'; toast('Not kaydedildi (yalnızca usta görür)'); }).catch(fail).then(function () { bt.disabled = false; }); };
      var jc = document.getElementById('spx-jc'); host.insertBefore(ex, jc ? jc.nextSibling : host.firstChild);
    } else if (!TN.dirty && document.activeElement !== ex.querySelector('textarea')) { var t2 = ex.querySelector('textarea'); if (t2.value !== (JC.j.tech_note || '')) t2.value = JC.j.tech_note || ''; }
  }
  setInterval(tnCard, 1000);
  function tnTech() {
    var dm = location.pathname.match(/^\/tech\/jobs\/([^/]+)/), ex = document.getElementById('spx-tnt');
    if (!document.body.classList.contains('spx-tech') || !localStorage.getItem('token')) { if (ex) ex.remove(); return; }
    slaLoad(false); var nt = SLA.nt; if (!nt) return;
    if (dm) {
      var n = nt[dm[1]], host = document.querySelector('[data-testid="tech-job-detail"]');
      if (!n || !host) { if (ex) ex.remove(); return; }
      if (!ex) { ex = document.createElement('div'); ex.id = 'spx-tnt'; ex.className = 'notranslate'; ex.style.cssText = 'border:2px solid #f59e0b;background:#fffbeb;border-radius:12px;padding:11px 13px;margin-bottom:12px;font-size:14px;line-height:1.5;color:#78350f'; host.insertBefore(ex, host.firstChild); }
      var h = '<b>📌 Yönetim notu</b><div style="white-space:pre-wrap;margin-top:3px">' + esc(n.t) + '</div>'; if (ex.getAttribute('data-h') !== h) { ex.setAttribute('data-h', h); ex.innerHTML = h; }
    } else {
      if (ex) ex.remove();
      Array.prototype.forEach.call(document.querySelectorAll('div.font-display'), function (nm) {
        var tx = (nm.textContent || '').trim(), card = nm.closest('.rounded-xl'); if (!tx || !card || nm.children.length) return;
        var hit = null; Object.keys(nt).forEach(function (k) { if (nt[k].c === tx && nt[k].n && card.textContent.indexOf(nt[k].n) > -1) hit = nt[k]; });
        var nx = nm.nextElementSibling; while (nx && nx.classList && nx.classList.contains('spx-sla')) nx = nx.nextElementSibling;
        var tag = card.querySelector('.spx-tnc');
        if (hit && !tag) { tag = document.createElement('div'); tag.className = 'spx-tnc'; tag.style.cssText = 'display:inline-block;margin:5px 0 0 6px;padding:4px 10px;border-radius:99px;background:#fef3c7;color:#92400e;font-weight:700;font-size:12.5px'; tag.textContent = '📌 Yönetim notu var'; nm.parentNode.insertBefore(tag, nm.nextSibling); }
        else if (!hit && tag) tag.remove();
      });
    }
  }
  setInterval(tnTech, 800);
  function phBlock(e) {
    var b = e.target && e.target.closest ? e.target.closest('button') : null; if (!b && e.type === 'click') return;
    var box = (b || e.target).closest('[role="dialog"]') || (b || e.target).closest('form'); if (!box) return;
    if (b && /vazge|iptal|kapat|cancel|close/i.test((b.textContent || '') + (b.getAttribute('aria-label') || ''))) return;
    var bad = null; phInputs().forEach(function (x) { if (!bad && box.contains(x[0]) && (phState(x[0], x[1]) === 'bad' || (x[1] && phState(x[0], x[1]) === 'empty' && b && /kaydet|olu[sş]tur|ekle|g[uü]ncelle/i.test(b.textContent || '')))) bad = x[0]; });
    if (!bad) return;
    if (b && !/kaydet|olu[sş]tur|ekle|g[uü]ncelle|kay[ıi]t/i.test(b.textContent || '')) return;
    e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation(); toast('Telefon numarası eksik veya hatalı — +90 sonrası 10 hane girin'); try { bad.focus(); } catch (x) { }
  }
  document.addEventListener('click', phBlock, true); document.addEventListener('submit', phBlock, true);

  /* ---------- admin: usta detayı (il/ilçe, hizmet grubu, marka, özel not) + giriş bilgisi WhatsApp'ı ---------- */
  var ILLER = 'Adana,Adıyaman,Afyonkarahisar,Ağrı,Aksaray,Amasya,Ankara,Antalya,Ardahan,Artvin,Aydın,Balıkesir,Bartın,Batman,Bayburt,Bilecik,Bingöl,Bitlis,Bolu,Burdur,Bursa,Çanakkale,Çankırı,Çorum,Denizli,Diyarbakır,Düzce,Edirne,Elazığ,Erzincan,Erzurum,Eskişehir,Gaziantep,Giresun,Gümüşhane,Hakkari,Hatay,Iğdır,Isparta,İstanbul,İzmir,Kahramanmaraş,Karabük,Karaman,Kars,Kastamonu,Kayseri,Kilis,Kırıkkale,Kırklareli,Kırşehir,Kocaeli,Konya,Kütahya,Malatya,Manisa,Mardin,Mersin,Muğla,Muş,Nevşehir,Niğde,Ordu,Osmaniye,Rize,Sakarya,Samsun,Siirt,Sinop,Sivas,Şanlıurfa,Şırnak,Tekirdağ,Tokat,Trabzon,Tunceli,Uşak,Van,Yalova,Yozgat,Zonguldak'.split(',');
  var TGRP = [['kombi', 'Kombi'], ['klima', 'Klima'], ['beyaz-esya', 'Beyaz eşya'], ['televizyon', 'Televizyon'], ['sofben', 'Şofben'], ['ocak-firin', 'Ocak / Fırın'], ['diger', 'Diğer']];
  var TPL = null, TPLT = 0, TPLB = false;
  var TOPEN = '';
  function techProfInline(id) {
    var card = document.querySelector('[data-testid="tech-card-' + id + '"]'); if (!card) { TOPEN = id; return; }
    var ex = card.querySelector('.spx-tf'); if (ex) { ex.remove(); return; }
    pcall('GET', '/technicians/' + id + '/profile').then(function (d) {
      if (card.querySelector('.spx-tf')) return;
      var p = d.profile || {}, o = document.createElement('div'); o.className = 'spx-tf notranslate'; o.style.cssText = 'margin-top:12px;border-top:1px dashed #cbd5e1;padding-top:12px';
      var fi = 'width:100%;padding:9px 10px;border:1px solid #cbd5e1;border-radius:8px;font:inherit;margin-top:3px;background:#fff;color:#0f172a;box-sizing:border-box';
      var lb = 'display:block;font-size:11px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.03em';
      var dl = 'td-il-' + id;
      o.innerHTML = '<div style="color:#64748b;font-size:12px;margin-bottom:8px">Tamamlanan iş: <b>' + (d.completed_jobs || 0) + '</b>' + (d.created_at ? ' · Kayıt: ' + new Date(d.created_at).toLocaleDateString('tr-TR') : '') + '</div>' +
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">' +
        '<div><label style="' + lb + '">İl</label><select data-f="city" style="' + fi + '">' + selOpts(TRK, trCity(p.city) || p.city || '', 'İl seçin') + '</select></div>' +
        '<div><label style="' + lb + '">Seçili ilçe sayısı</label><div data-dc style="' + fi + ';background:#f8fafc">0</div></div></div>' +
        '<label style="' + lb + ';margin-top:10px">Hizmet verdiği ilçeler</label><input type="hidden" data-f="districts" value="' + esc((p.districts || []).join(', ')) + '"><div data-dw style="display:flex;flex-wrap:wrap;gap:5px;margin-top:5px;max-height:170px;overflow:auto;border:1px solid #cbd5e1;border-radius:8px;padding:8px;background:#fff"></div><div style="display:flex;gap:12px;margin-top:4px;font-size:12px"><a data-da="all" style="color:#1d4ed8;font-weight:700;cursor:pointer">Tüm ilçeler</a><a data-da="none" style="color:#1d4ed8;font-weight:700;cursor:pointer">Temizle</a></div>' +
        '<label style="' + lb + ';margin-top:10px">Baktığı servis grupları</label><div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:5px">' + TGRP.map(function (g) { var on = (p.service_groups || []).indexOf(g[0]) >= 0; return '<label style="display:flex;align-items:center;gap:5px;border:1px solid #cbd5e1;border-radius:99px;padding:4px 10px;cursor:pointer;font-size:13px"><input type="checkbox" data-g="' + g[0] + '"' + (on ? ' checked' : '') + '> ' + g[1] + '</label>'; }).join('') + '</div>' +
        '<label style="' + lb + ';margin-top:10px">Uzman markalar (virgülle)</label><input data-f="brands" value="' + esc((p.brands || []).join(', ')) + '" placeholder="Demirdöküm, Vaillant" style="' + fi + '">' +
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px"><div><label style="' + lb + '">Deneyim (yıl)</label><input data-f="exp" type="number" min="0" max="60" value="' + (p.experience_years || '') + '" style="' + fi + '"></div><div><label style="' + lb + '">İşe başlama</label><input data-f="start" type="date" value="' + esc(p.start_date || '') + '" style="' + fi + '"></div></div>' +
        '<label style="' + lb + ';margin-top:10px">Çalışma gün / saat</label><input data-f="wh" value="' + esc(p.work_hours || '') + '" placeholder="Hafta içi 08:00-19:00" style="' + fi + '">' +
        '<label style="display:flex;align-items:center;gap:6px;margin-top:10px;font-size:13px"><input type="checkbox" data-f="veh"' + (p.has_vehicle ? ' checked' : '') + '> Kendi aracı var</label>' +
        '<label style="' + lb + ';margin-top:10px">Adres</label><input data-f="adr" value="' + esc(p.address || '') + '" style="' + fi + '">' +
        '<label style="' + lb + ';margin-top:10px">Özel not <span style="text-transform:none;font-weight:500">(yalnız yönetim görür)</span></label><textarea data-f="note" rows="3" style="' + fi + '">' + esc(d.note || '') + '</textarea>' +
        '<div style="display:flex;gap:8px;margin-top:12px"><button data-s="save" style="flex:1;border:0;background:#f27a1a;color:#fff;border-radius:9px;padding:10px;font-weight:700;cursor:pointer">Kaydet</button><button data-s="cancel" style="border:1px solid #cbd5e1;background:#fff;border-radius:9px;padding:10px 16px;font-weight:600;cursor:pointer">Kapat</button></div><div data-m style="margin-top:6px;font-size:13px;font-weight:600"></div>';
      card.appendChild(o);
      var q = function (f) { return o.querySelector('[data-f="' + f + '"]'); };
      var chosen = (p.districts || []).slice();
      var drawD = function () {
        var city = trCity(q('city').value), L = (TRD[city] || []).slice(); chosen.forEach(function (x) { if (L.indexOf(x) < 0) L.push(x); });
        var w = o.querySelector('[data-dw]'); w.innerHTML = L.length ? L.map(function (d) { var on = chosen.indexOf(d) >= 0; return '<label style="display:inline-flex;align-items:center;gap:4px;border:1px solid ' + (on ? '#0a1f44' : '#cbd5e1') + ';background:' + (on ? '#0a1f44' : '#f8fafc') + ';color:' + (on ? '#fff' : '#0f172a') + ';border-radius:99px;padding:3px 10px;font-size:12.5px;font-weight:600;cursor:pointer"><input type="checkbox" data-d="' + esc(d) + '"' + (on ? ' checked' : '') + ' style="display:none">' + esc(d) + '</label>'; }).join('') : '<span style="color:#94a3b8;font-size:12px">Önce il seçin</span>';
        q('districts').value = chosen.join(', '); o.querySelector('[data-dc]').textContent = chosen.length;
      };
      drawD();
      q('city').onchange = function () { chosen = []; drawD(); };
      o.querySelector('[data-dw]').onchange = function (e) { var c = e.target; if (!c.getAttribute('data-d')) return; var d = c.getAttribute('data-d'), i = chosen.indexOf(d); if (c.checked && i < 0) chosen.push(d); if (!c.checked && i >= 0) chosen.splice(i, 1); drawD(); };
      o.addEventListener('click', function (e) { var a = e.target.closest('a[data-da]'); if (!a) return; chosen = a.getAttribute('data-da') === 'all' ? (TRD[trCity(q('city').value)] || []).slice() : []; drawD(); });
      o.onclick = function (e) { e.stopPropagation(); var b = e.target.closest('button[data-s]'); if (!b) return; if (b.getAttribute('data-s') === 'cancel') { o.remove(); return; }
        var g = []; Array.prototype.forEach.call(o.querySelectorAll('input[data-g]'), function (c) { if (c.checked) g.push(c.getAttribute('data-g')); });
        pcall('PUT', '/technicians/' + id + '/profile', { city: q('city').value, districts: q('districts').value, service_groups: g, brands: q('brands').value, experience_years: q('exp').value, start_date: q('start').value, work_hours: q('wh').value, has_vehicle: q('veh').checked, address: q('adr').value, note: q('note').value })
          .then(function () { toast('Usta detayı kaydedildi'); TPL = null; TPLT = 0; var m = o.querySelector('[data-m]'); m.style.color = '#16a34a'; m.textContent = '✔ Kaydedildi'; }).catch(function (er) { var m = o.querySelector('[data-m]'); m.style.color = '#b91c1c'; m.textContent = er.message; }); };
    }).catch(fail);
  }
  function techProfModal(id) { if (!/^\/admin\/technicians/.test(location.pathname)) { TOPEN = id; goto('/admin/technicians'); } else techProfInline(id); }
  function techCreds(id, name) {
    if (!confirm(name + ' için YENİ şifre oluşturulacak (eski şifresi geçersiz olur) ve giriş bilgisi WhatsApp mesajı hazırlanacak. Devam edilsin mi?')) return;
    pcall('POST', '/technicians/' + id + '/reset-credentials', {}).then(function (r) { welCard(r.name, r.phone, r.email, r.password, r.id); }).catch(fail);
  }
  var TF = { city: '', dist: '', grp: '', brand: '', veh: false, free: '' };
  function nrm(x) { return String(x || '').toLocaleLowerCase('tr').replace(/ç/g, 'c').replace(/ğ/g, 'g').replace(/ı/g, 'i').replace(/ö/g, 'o').replace(/ş/g, 's').replace(/ü/g, 'u').trim(); }
  function techFilterHit(id) {
    var p = (TPL && TPL[id]) || {};
    if (TF.city && nrm(p.city) !== nrm(TF.city)) return false;
    if (TF.dist && (p.districts || []).map(nrm).indexOf(nrm(TF.dist)) < 0) return false;
    if (TF.grp && (p.service_groups || []).indexOf(TF.grp) < 0) return false;
    if (TF.brand && (p.brands || []).map(nrm).indexOf(nrm(TF.brand)) < 0) return false;
    if (TF.veh && !p.has_vehicle) return false;
    return true;
  }
  function techFilterBar(pg) {
    if (!TPL) return;
    var ex = document.getElementById('spx-tf2'), cities = {}, dists = {}, brands = {};
    Object.keys(TPL).forEach(function (id) { var p = TPL[id]; if (p.city) cities[p.city] = 1; if (!TF.city || nrm(p.city) === nrm(TF.city)) (p.districts || []).forEach(function (d) { dists[d] = 1; }); (p.brands || []).forEach(function (b) { brands[b] = 1; }); });
    var sig = JSON.stringify([Object.keys(cities), Object.keys(dists), Object.keys(brands), TF]);
    if (ex && ex.getAttribute('data-sig') === sig) return;
    if (ex) ex.remove();
    var s = document.querySelector('[data-testid="tech-search"]'), row = s && s.closest('.flex-wrap');
    if (!row) { var c0 = pg.querySelector('[data-testid^="tech-card-"]'); row = c0 && c0.parentElement; }
    if (!row) return;
    var rowFirst = !(s && s.closest('.flex-wrap'));
    var opt = function (list, cur, ph) { return '<option value="">' + ph + '</option>' + list.sort(function (a, b) { return a.localeCompare(b, 'tr'); }).map(function (x) { return '<option value="' + esc(x) + '"' + (x === cur ? ' selected' : '') + '>' + esc(x) + '</option>'; }).join(''); };
    var st = 'border:1px solid #cbd5e1;background:#fff;border-radius:8px;padding:6px 10px;font-size:13px;color:#0a1f44';
    ex = document.createElement('div'); ex.id = 'spx-tf2'; ex.setAttribute('data-sig', sig); ex.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:8px';
    ex.innerHTML = '<span style="font-size:12px;font-weight:700;color:#64748b">📍 Bölge filtresi:</span>' +
      '<select data-k="city" style="' + st + '">' + opt(Object.keys(cities), TF.city, 'Tüm iller') + '</select>' +
      '<select data-k="dist" style="' + st + '">' + opt(Object.keys(dists), TF.dist, 'Tüm ilçeler') + '</select>' +
      '<select data-k="grp" style="' + st + '"><option value="">Tüm servis grupları</option>' + TGRP.map(function (g) { return '<option value="' + g[0] + '"' + (TF.grp === g[0] ? ' selected' : '') + '>' + g[1] + '</option>'; }).join('') + '</select>' +
      '<select data-k="brand" style="' + st + '">' + opt(Object.keys(brands), TF.brand, 'Tüm markalar') + '</select>' +
      '<label style="display:flex;align-items:center;gap:5px;font-size:13px"><input type="checkbox" data-k="veh"' + (TF.veh ? ' checked' : '') + '> Araçlı</label>' +
      ((TF.city || TF.dist || TF.grp || TF.brand || TF.veh) ? '<button data-k="clr" style="border:0;background:none;color:#1d4ed8;font-weight:700;font-size:13px;cursor:pointer">Temizle</button>' : '');
    ex.onchange = function (e) { var k = e.target.getAttribute('data-k'); if (!k) return; if (k === 'veh') TF.veh = e.target.checked; else { TF[k] = e.target.value; if (k === 'city') TF.dist = ''; } techQuick(); };
    ex.onclick = function (e) { if (e.target.getAttribute('data-k') === 'clr') { TF.city = TF.dist = TF.grp = TF.brand = ''; TF.veh = false; techQuick(); } };
    if (rowFirst) row.parentElement.insertBefore(ex, row); else row.parentElement.insertBefore(ex, row.nextSibling);
  }

  /* ---------- admin: usta iş geçmişi (kaç iş yapmış, ayrıntıları) ---------- */
  var STL = { yeni: 'Yeni', atandi: 'Atandı', yolda: 'Yolda', basladi: 'Başladı', tamamlandi: 'Tamamlandı', faturalandi: 'Faturalandı', iptal: 'İptal' };
  function techHistory(id, name) {
    var card = document.querySelector('[data-testid="tech-card-' + id + '"]'); if (!card) return;
    var ex = card.querySelector('.spx-th'); if (ex) { ex.remove(); return; }
    var o = document.createElement('div'); o.className = 'spx-th notranslate'; o.style.cssText = 'margin-top:12px;border-top:1px dashed #cbd5e1;padding-top:12px;font-size:13px'; o.innerHTML = '<span style="color:#64748b">Yükleniyor…</span>';
    card.appendChild(o); o.onclick = function (e) { e.stopPropagation(); };
    pcall('GET', '/jobs?technician_id=' + encodeURIComponent(id)).then(function (rows) {
      rows = (rows || []).filter(function (j) { return j.assigned_technician_id === id; }).sort(function (a, b) { return String(b.created_at || '').localeCompare(String(a.created_at || '')); });
      var done = rows.filter(function (j) { return j.status === 'tamamlandi' || j.status === 'faturalandi'; }), canc = rows.filter(function (j) { return j.status === 'iptal'; }), open = rows.length - done.length - canc.length;
      var ym = new Date().toISOString().slice(0, 7), mon = done.filter(function (j) { return String(j.completed_at || j.updated_at || '').slice(0, 7) === ym; }).length;
      var rt = rows.map(function (j) { return +j.customer_rating || (j.survey && +j.survey.rating) || 0; }).filter(Boolean), avg = rt.length ? (rt.reduce(function (a, b) { return a + b; }, 0) / rt.length).toFixed(1) : '-';
      var chip = function (k, v, c) { return '<div style="background:' + c + ';border-radius:10px;padding:8px 12px;min-width:92px"><div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase">' + k + '</div><div style="font-size:20px;font-weight:800;color:#0a1f44">' + v + '</div></div>'; };
      var show = 15;
      var draw = function () {
        var h = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px">' + chip('Toplam iş', rows.length, '#eff6ff') + chip('Tamamlanan', done.length, '#f0fdf4') + chip('Bu ay', mon, '#f0fdf4') + chip('Açık', open, '#fff7ed') + chip('İptal', canc.length, '#fef2f2') + chip('Ort. puan', avg, '#faf5ff') + '</div>';
        if (!rows.length) h += '<div style="color:#94a3b8">Bu ustaya atanmış kayıt yok.</div>';
        else {
          h += '<div style="overflow:auto"><table style="width:100%;border-collapse:collapse;font-size:12.5px"><thead><tr style="text-align:left;color:#64748b"><th style="padding:5px 6px">Kayıt</th><th style="padding:5px 6px">Tarih</th><th style="padding:5px 6px">Müşteri</th><th style="padding:5px 6px">Cihaz</th><th style="padding:5px 6px">Durum</th></tr></thead><tbody>';
          rows.slice(0, show).forEach(function (j) { h += '<tr style="border-top:1px solid #e2e8f0"><td style="padding:5px 6px"><a data-j="' + esc(j.id) + '" style="color:#1d4ed8;font-weight:700;cursor:pointer">' + esc(j.job_number) + '</a></td><td style="padding:5px 6px;white-space:nowrap">' + esc(new Date(j.created_at).toLocaleDateString('tr-TR')) + '</td><td style="padding:5px 6px">' + esc(j.customer_name || '') + '</td><td style="padding:5px 6px">' + esc([j.device_brand_name, j.device_type].filter(Boolean).join(' ')) + '</td><td style="padding:5px 6px">' + esc(STL[j.status] || j.status) + '</td></tr>'; });
          h += '</tbody></table></div>';
          if (rows.length > show) h += '<button data-more style="margin-top:8px;border:1px solid #cbd5e1;background:#fff;border-radius:8px;padding:6px 12px;font-weight:700;cursor:pointer">Daha fazla göster (' + (rows.length - show) + ' kayıt daha)</button>';
        }
        o.innerHTML = '<div style="font-weight:800;color:#0a1f44;margin-bottom:8px">📈 ' + esc(name) + ' — iş geçmişi</div>' + h;
        var mb = o.querySelector('[data-more]'); if (mb) mb.onclick = function () { show += 30; draw(); };
        [].forEach.call(o.querySelectorAll('a[data-j]'), function (a) { a.onclick = function () { goto('/admin/jobs/' + a.getAttribute('data-j')); }; });
      };
      draw();
    }).catch(function (er) { o.innerHTML = '<span style="color:#b91c1c">' + esc(er.message) + '</span>'; });
  }
  function techExtras() {
    var pg = document.querySelector('[data-testid="technicians-page"]'); if (!pg || !/^\/admin\/technicians\/?$/.test(location.pathname)) return;
    if ((!TPL || Date.now() - TPLT > 30000) && !TPLB) { TPLB = true; pcall('GET', '/technicians').then(function (a) { var m = {}; (a || []).forEach(function (x) { var q = {}; var pr = x.profile || {}; Object.keys(pr).forEach(function (k) { q[k] = pr[k]; }); q._iban = x.iban || ''; m[x.id] = q; }); TPL = m; TPLT = Date.now(); }).catch(function () { TPL = TPL || {}; TPLT = Date.now(); }).then(function () { TPLB = false; }); }
    Array.prototype.forEach.call(pg.querySelectorAll('[data-testid^="tech-card-"]'), function (c) {
      var id = c.getAttribute('data-testid').slice(10), p = (TPL && TPL[id]) || {}, name = ((c.querySelector('.font-semibold') || {}).textContent) || 'Usta';
      var sig = JSON.stringify([p.city, p.districts, p.service_groups, p._iban, !!TPL]), ex = c.querySelector('.spx-tp');
      if (ex && ex.getAttribute('data-sig') === sig) return;
      if (ex) ex.remove();
      var chips = '';
      var place = [p.city, (p.districts || []).slice(0, 3).join(', ') + ((p.districts || []).length > 3 ? ' +' + ((p.districts || []).length - 3) : '')].filter(function (x) { return x && x.trim(); }).join(' · ');
      if (place) chips += '<span style="background:#eff6ff;color:#1d4ed8;border-radius:99px;padding:3px 10px;font-size:12px;font-weight:600">📍 ' + esc(place) + '</span>';
      (p.service_groups || []).forEach(function (g) { var t = TGRP.filter(function (x) { return x[0] === g; })[0]; chips += '<span style="background:#fff7ed;color:#c2570c;border-radius:99px;padding:3px 10px;font-size:12px;font-weight:600">' + esc(t ? t[1] : g) + '</span>'; });
      var d = document.createElement('div'); d.className = 'spx-tp'; d.setAttribute('data-sig', sig); d.style.cssText = 'margin-top:12px;display:flex;flex-direction:column;gap:8px';
      var ibn = String(p._iban || '').replace(/\s+/g, '').toUpperCase(), ibh = ibn ? '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;background:#f6f7f9;border-radius:8px;padding:6px 10px"><span style="font-size:11px;color:#64748b;font-weight:700">IBAN</span><span style="font-family:monospace;font-size:13px;color:#0a1f44;font-weight:600">' + esc(ibn.replace(/(.{4})/g, '$1 ').trim()) + '</span><button data-a="cpiban" data-v="' + esc(ibn) + '" style="border:1px solid #cbd5e1;background:#fff;border-radius:6px;padding:2px 8px;font-size:12px;cursor:pointer">Kopyala</button></div>' : '<div style="font-size:12px;color:#94a3b8">IBAN girilmemiş</div>';
      d.innerHTML = ibh + (chips ? '<div style="display:flex;flex-wrap:wrap;gap:6px">' + chips + '</div>' : '<div style="font-size:12px;color:#94a3b8">Bölge / uzmanlık bilgisi girilmemiş</div>') +
        '<div style="display:flex;gap:8px;flex-wrap:wrap"><button data-a="det" style="border:1px solid #cbd5e1;background:#fff;color:#0a1f44;border-radius:8px;padding:6px 12px;font-weight:700;font-size:13px;cursor:pointer">📋 Detay / Not ▾</button><button data-a="hist" style="border:1px solid #cbd5e1;background:#fff;color:#0a1f44;border-radius:8px;padding:6px 12px;font-weight:700;font-size:13px;cursor:pointer">📈 İş Geçmişi ▾</button><button data-a="wa" style="border:1px solid #86efac;background:#f0fdf4;color:#15803d;border-radius:8px;padding:6px 12px;font-weight:700;font-size:13px;cursor:pointer">💬 Giriş bilgisi gönder</button></div>';
      d.onclick = function (e) { var b = e.target.closest('button[data-a]'); if (!b) return; e.stopPropagation(); var ac = b.getAttribute('data-a'); if (ac === 'cpiban') { var v = b.getAttribute('data-v'); (navigator.clipboard ? navigator.clipboard.writeText(v) : Promise.reject()).catch(function () { var t = document.createElement('textarea'); t.value = v; document.body.appendChild(t); t.select(); try { document.execCommand('copy'); } catch (er) { } t.remove(); }); b.textContent = 'Kopyalandı'; return; } if (ac === 'det') techProfInline(id); else if (ac === 'hist') techHistory(id, name); else techCreds(id, name); };
      c.insertBefore(d, c.querySelector('.spx-tf'));
    });
    techFilterBar(pg);
    if (TOPEN && pg.querySelector('[data-testid="tech-card-' + TOPEN + '"] .spx-tp')) { var tt = TOPEN; TOPEN = ''; techProfInline(tt); }
  }
  setInterval(techExtras, 900);


  /* ---------- Türkiye il → ilçe verisi + admin panelindeki tüm adres alanlarında bağımlı il/ilçe seçimi ---------- */
  var TRD = {"Adana":["Aladağ","Ceyhan","Çukurova","Feke","İmamoğlu","Karaisalı","Karataş","Kozan","Pozantı","Saimbeyli","Sarıçam","Seyhan","Tufanbeyli","Yumurtalık","Yüreğir"],"Adıyaman":["Besni","Çelikhan","Gerger","Gölbaşı","Kahta","Merkez","Samsat","Sincik","Tut"],"Afyonkarahisar":["Başmakçı","Bayat","Bolvadin","Çay","Çobanlar","Dazkırı","Dinar","Emirdağ","Evciler","Hocalar","İhsaniye","İscehisar","Kızılören","Merkez","Sandıklı","Sinanpaşa","Sultandağı","Şuhut"],"Ağrı":["Diyadin","Doğubayazıt","Eleşkirt","Hamur","Merkez","Patnos","Taşlıçay","Tutak"],"Aksaray":["Ağaçören","Eskil","Gülağaç","Güzelyurt","Merkez","Ortaköy","Sarıyahşi","Sultanhanı"],"Amasya":["Göynücek","Gümüşhacıköy","Hamamözü","Merkez","Merzifon","Suluova","Taşova"],"Ankara":["Akyurt","Altındağ","Ayaş","Bala","Beypazarı","Çamlıdere","Çankaya","Çubuk","Elmadağ","Etimesgut","Evren","Gölbaşı","Güdül","Haymana","Kahramankazan","Kalecik","Keçiören","Kızılcahamam","Mamak","Nallıhan","Polatlı","Pursaklar","Sincan","Şereflikoçhisar","Yenimahalle"],"Antalya":["Akseki","Aksu","Alanya","Demre","Döşemealtı","Elmalı","Finike","Gazipaşa","Gündoğmuş","İbradı","Kaş","Kemer","Kepez","Konyaaltı","Korkuteli","Kumluca","Manavgat","Muratpaşa","Serik"],"Ardahan":["Çıldır","Damal","Göle","Hanak","Merkez","Posof"],"Artvin":["Ardanuç","Arhavi","Borçka","Hopa","Kemalpaşa","Merkez","Murgul","Şavşat","Yusufeli"],"Aydın":["Bozdoğan","Buharkent","Çine","Didim","Efeler","Germencik","İncirliova","Karacasu","Karpuzlu","Koçarlı","Köşk","Kuşadası","Kuyucak","Nazilli","Söke","Sultanhisar","Yenipazar"],"Balıkesir":["Altıeylül","Ayvalık","Balya","Bandırma","Bigadiç","Burhaniye","Dursunbey","Edremit","Erdek","Gömeç","Gönen","Havran","İvrindi","Karesi","Kepsut","Manyas","Marmara","Savaştepe","Sındırgı","Susurluk"],"Bartın":["Amasra","Kurucaşile","Merkez","Ulus"],"Batman":["Beşiri","Gercüş","Hasankeyf","Kozluk","Merkez","Sason"],"Bayburt":["Aydıntepe","Demirözü","Merkez"],"Bilecik":["Bozüyük","Gölpazarı","İnhisar","Merkez","Osmaneli","Pazaryeri","Söğüt","Yenipazar"],"Bingöl":["Adaklı","Genç","Karlıova","Kiğı","Merkez","Solhan","Yayladere","Yedisu"],"Bitlis":["Adilcevaz","Ahlat","Güroymak","Hizan","Merkez","Mutki","Tatvan"],"Bolu":["Dörtdivan","Gerede","Göynük","Kıbrıscık","Mengen","Merkez","Mudurnu","Seben","Yeniçağa"],"Burdur":["Ağlasun","Altınyayla","Bucak","Çavdır","Çeltikçi","Gölhisar","Karamanlı","Kemer","Merkez","Tefenni","Yeşilova"],"Bursa":["Büyükorhan","Gemlik","Gürsu","Harmancık","İnegöl","İznik","Karacabey","Keles","Kestel","Mudanya","Mustafakemalpaşa","Nilüfer","Orhaneli","Orhangazi","Osmangazi","Yenişehir","Yıldırım"],"Çanakkale":["Ayvacık","Bayramiç","Biga","Bozcaada","Çan","Eceabat","Ezine","Gelibolu","Gökçeada","Lapseki","Merkez","Yenice"],"Çankırı":["Atkaracalar","Bayramören","Çerkeş","Eldivan","Ilgaz","Kızılırmak","Korgun","Kurşunlu","Merkez","Orta","Şabanözü","Yapraklı"],"Çorum":["Alaca","Bayat","Boğazkale","Dodurga","İskilip","Kargı","Laçin","Mecitözü","Merkez","Oğuzlar","Ortaköy","Osmancık","Sungurlu","Uğurludağ"],"Denizli":["Acıpayam","Babadağ","Baklan","Bekilli","Beyağaç","Bozkurt","Buldan","Çal","Çameli","Çardak","Çivril","Güney","Honaz","Kale","Merkezefendi","Pamukkale","Sarayköy","Serinhisar","Tavas"],"Diyarbakır":["Bağlar","Bismil","Çermik","Çınar","Çüngüş","Dicle","Eğil","Ergani","Hani","Hazro","Kayapınar","Kocaköy","Kulp","Lice","Silvan","Sur","Yenişehir"],"Düzce":["Akçakoca","Cumayeri","Çilimli","Gölyaka","Gümüşova","Kaynaşlı","Merkez","Yığılca"],"Edirne":["Enez","Havsa","İpsala","Keşan","Lalapaşa","Meriç","Merkez","Süloğlu","Uzunköprü"],"Elazığ":["Ağın","Alacakaya","Arıcak","Baskil","Karakoçan","Keban","Kovancılar","Maden","Merkez","Palu","Sivrice"],"Erzincan":["Çayırlı","İliç","Kemah","Kemaliye","Merkez","Otlukbeli","Refahiye","Tercan","Üzümlü"],"Erzurum":["Aşkale","Aziziye","Çat","Hınıs","Horasan","İspir","Karaçoban","Karayazı","Köprüköy","Narman","Oltu","Olur","Palandöken","Pasinler","Pazaryolu","Şenkaya","Tekman","Tortum","Uzundere","Yakutiye"],"Eskişehir":["Alpu","Beylikova","Çifteler","Günyüzü","Han","İnönü","Mahmudiye","Mihalgazi","Mihalıççık","Odunpazarı","Sarıcakaya","Seyitgazi","Sivrihisar","Tepebaşı"],"Gaziantep":["Araban","İslahiye","Karkamış","Nizip","Nurdağı","Oğuzeli","Şahinbey","Şehitkamil","Yavuzeli"],"Giresun":["Alucra","Bulancak","Çamoluk","Çanakçı","Dereli","Doğankent","Espiye","Eynesil","Görele","Güce","Keşap","Merkez","Piraziz","Şebinkarahisar","Tirebolu","Yağlıdere"],"Gümüşhane":["Kelkit","Köse","Kürtün","Merkez","Şiran","Torul"],"Hakkari":["Çukurca","Derecik","Merkez","Şemdinli","Yüksekova"],"Hatay":["Altınözü","Antakya","Arsuz","Belen","Defne","Dörtyol","Erzin","Hassa","İskenderun","Kırıkhan","Kumlu","Payas","Reyhanlı","Samandağ","Yayladağı"],"Iğdır":["Aralık","Karakoyunlu","Merkez","Tuzluca"],"Isparta":["Aksu","Atabey","Eğirdir","Gelendost","Gönen","Keçiborlu","Merkez","Senirkent","Sütçüler","Şarkikaraağaç","Uluborlu","Yalvaç","Yenişarbademli"],"İstanbul":["Adalar","Arnavutköy","Ataşehir","Avcılar","Bağcılar","Bahçelievler","Bakırköy","Başakşehir","Bayrampaşa","Beşiktaş","Beykoz","Beylikdüzü","Beyoğlu","Büyükçekmece","Çatalca","Çekmeköy","Esenler","Esenyurt","Eyüpsultan","Fatih","Gaziosmanpaşa","Güngören","Kadıköy","Kağıthane","Kartal","Küçükçekmece","Maltepe","Pendik","Sancaktepe","Sarıyer","Silivri","Sultanbeyli","Sultangazi","Şile","Şişli","Tuzla","Ümraniye","Üsküdar","Zeytinburnu"],"İzmir":["Aliağa","Balçova","Bayındır","Bayraklı","Bergama","Beydağ","Bornova","Buca","Çeşme","Çiğli","Dikili","Foça","Gaziemir","Güzelbahçe","Karabağlar","Karaburun","Karşıyaka","Kemalpaşa","Kınık","Kiraz","Konak","Menderes","Menemen","Narlıdere","Ödemiş","Seferihisar","Selçuk","Tire","Torbalı","Urla"],"Kahramanmaraş":["Afşin","Andırın","Çağlayancerit","Dulkadiroğlu","Ekinözü","Elbistan","Göksun","Nurhak","Onikişubat","Pazarcık","Türkoğlu"],"Karabük":["Eflani","Eskipazar","Merkez","Ovacık","Safranbolu","Yenice"],"Karaman":["Ayrancı","Başyayla","Ermenek","Kazımkarabekir","Merkez","Sarıveliler"],"Kars":["Akyaka","Arpaçay","Digor","Kağızman","Merkez","Sarıkamış","Selim","Susuz"],"Kastamonu":["Abana","Ağlı","Araç","Azdavay","Bozkurt","Cide","Çatalzeytin","Daday","Devrekani","Doğanyurt","Hanönü","İhsangazi","İnebolu","Küre","Merkez","Pınarbaşı","Seydiler","Şenpazar","Taşköprü","Tosya"],"Kayseri":["Akkışla","Bünyan","Develi","Felahiye","Hacılar","İncesu","Kocasinan","Melikgazi","Özvatan","Pınarbaşı","Sarıoğlan","Sarız","Talas","Tomarza","Yahyalı","Yeşilhisar"],"Kırıkkale":["Bahşılı","Balışeyh","Çelebi","Delice","Karakeçili","Keskin","Merkez","Sulakyurt","Yahşihan"],"Kırklareli":["Babaeski","Demirköy","Kofçaz","Lüleburgaz","Merkez","Pehlivanköy","Pınarhisar","Vize"],"Kırşehir":["Akçakent","Akpınar","Boztepe","Çiçekdağı","Kaman","Merkez","Mucur"],"Kilis":["Elbeyli","Merkez","Musabeyli","Polateli"],"Kocaeli":["Başiskele","Çayırova","Darıca","Derince","Dilovası","Gebze","Gölcük","İzmit","Kandıra","Karamürsel","Kartepe","Körfez"],"Konya":["Ahırlı","Akören","Akşehir","Altınekin","Beyşehir","Bozkır","Cihanbeyli","Çeltik","Çumra","Derbent","Derebucak","Doğanhisar","Emirgazi","Ereğli","Güneysınır","Hadim","Halkapınar","Hüyük","Ilgın","Kadınhanı","Karapınar","Karatay","Kulu","Meram","Sarayönü","Selçuklu","Seydişehir","Taşkent","Tuzlukçu","Yalıhüyük","Yunak"],"Kütahya":["Altıntaş","Aslanapa","Çavdarhisar","Domaniç","Dumlupınar","Emet","Gediz","Hisarcık","Merkez","Pazarlar","Simav","Şaphane","Tavşanlı"],"Malatya":["Akçadağ","Arapgir","Arguvan","Battalgazi","Darende","Doğanşehir","Doğanyol","Hekimhan","Kale","Kuluncak","Pütürge","Yazıhan","Yeşilyurt"],"Manisa":["Ahmetli","Akhisar","Alaşehir","Demirci","Gölmarmara","Gördes","Kırkağaç","Köprübaşı","Kula","Salihli","Sarıgöl","Saruhanlı","Selendi","Soma","Şehzadeler","Turgutlu","Yunusemre"],"Mardin":["Artuklu","Dargeçit","Derik","Kızıltepe","Mazıdağı","Midyat","Nusaybin","Ömerli","Savur","Yeşilli"],"Mersin":["Akdeniz","Anamur","Aydıncık","Bozyazı","Çamlıyayla","Erdemli","Gülnar","Mezitli","Mut","Silifke","Tarsus","Toroslar","Yenişehir"],"Muğla":["Bodrum","Dalaman","Datça","Fethiye","Kavaklıdere","Köyceğiz","Marmaris","Menteşe","Milas","Ortaca","Seydikemer","Ula","Yatağan"],"Muş":["Bulanık","Hasköy","Korkut","Malazgirt","Merkez","Varto"],"Nevşehir":["Acıgöl","Avanos","Derinkuyu","Gülşehir","Hacıbektaş","Kozaklı","Merkez","Ürgüp"],"Niğde":["Altunhisar","Bor","Çamardı","Çiftlik","Merkez","Ulukışla"],"Ordu":["Akkuş","Altınordu","Aybastı","Çamaş","Çatalpınar","Çaybaşı","Fatsa","Gölköy","Gülyalı","Gürgentepe","İkizce","Kabadüz","Kabataş","Korgan","Kumru","Mesudiye","Perşembe","Ulubey","Ünye"],"Osmaniye":["Bahçe","Düziçi","Hasanbeyli","Kadirli","Merkez","Sumbas","Toprakkale"],"Rize":["Ardeşen","Çamlıhemşin","Çayeli","Derepazarı","Fındıklı","Güneysu","Hemşin","İkizdere","İyidere","Kalkandere","Merkez","Pazar"],"Sakarya":["Adapazarı","Akyazı","Arifiye","Erenler","Ferizli","Geyve","Hendek","Karapürçek","Karasu","Kaynarca","Kocaali","Pamukova","Sapanca","Serdivan","Söğütlü","Taraklı"],"Samsun":["19 Mayıs","Alaçam","Asarcık","Atakum","Ayvacık","Bafra","Canik","Çarşamba","Havza","İlkadım","Kavak","Ladik","Salıpazarı","Tekkeköy","Terme","Vezirköprü","Yakakent"],"Siirt":["Baykan","Eruh","Kurtalan","Merkez","Pervari","Şirvan","Tillo"],"Sinop":["Ayancık","Boyabat","Dikmen","Durağan","Erfelek","Gerze","Merkez","Saraydüzü","Türkeli"],"Sivas":["Akıncılar","Altınyayla","Divriği","Doğanşar","Gemerek","Gölova","Gürün","Hafik","İmranlı","Kangal","Koyulhisar","Merkez","Suşehri","Şarkışla","Ulaş","Yıldızeli","Zara"],"Şanlıurfa":["Akçakale","Birecik","Bozova","Ceylanpınar","Eyyübiye","Halfeti","Haliliye","Harran","Hilvan","Karaköprü","Siverek","Suruç","Viranşehir"],"Şırnak":["Beytüşşebap","Cizre","Güçlükonak","İdil","Merkez","Silopi","Uludere"],"Tekirdağ":["Çerkezköy","Çorlu","Ergene","Hayrabolu","Kapaklı","Malkara","Marmaraereğlisi","Muratlı","Saray","Süleymanpaşa","Şarköy"],"Tokat":["Almus","Artova","Başçiftlik","Erbaa","Merkez","Niksar","Pazar","Reşadiye","Sulusaray","Turhal","Yeşilyurt","Zile"],"Trabzon":["Akçaabat","Araklı","Arsin","Beşikdüzü","Çarşıbaşı","Çaykara","Dernekpazarı","Düzköy","Hayrat","Köprübaşı","Maçka","Of","Ortahisar","Sürmene","Şalpazarı","Tonya","Vakfıkebir","Yomra"],"Tunceli":["Çemişgezek","Hozat","Mazgirt","Merkez","Nazımiye","Ovacık","Pertek","Pülümür"],"Uşak":["Banaz","Eşme","Karahallı","Merkez","Sivaslı","Ulubey"],"Van":["Bahçesaray","Başkale","Çaldıran","Çatak","Edremit","Erciş","Gevaş","Gürpınar","İpekyolu","Muradiye","Özalp","Saray","Tuşba"],"Yalova":["Altınova","Armutlu","Çınarcık","Çiftlikköy","Merkez","Termal"],"Yozgat":["Akdağmadeni","Aydıncık","Boğazlıyan","Çandır","Çayıralan","Çekerek","Kadışehri","Merkez","Saraykent","Sarıkaya","Sorgun","Şefaatli","Yenifakılı","Yerköy"],"Zonguldak":["Alaplı","Çaycuma","Devrek","Ereğli","Gökçebey","Kilimli","Kozlu","Merkez"]};
  var TRK = Object.keys(TRD).sort(function (a, b) { return a.localeCompare(b, 'tr'); });
  function trCity(v) { var n = nrm(v); for (var i = 0; i < TRK.length; i++) if (nrm(TRK[i]) === n) return TRK[i]; return ''; }
  function trDist(city, v) { var L = TRD[trCity(city)] || [], n = nrm(v); for (var i = 0; i < L.length; i++) if (nrm(L[i]) === n) return L[i]; return ''; }
  function setNative(inp, v) { var set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; set.call(inp, v); inp.dispatchEvent(new Event('input', { bubbles: true })); }
  var SELST = 'width:100%;height:40px;border:1px solid #e2e8f0;border-radius:6px;padding:0 10px;background:#fff;font-size:14px;color:#0f172a';
  function selOpts(list, cur, ph) {
    var h = '<option value="">' + ph + '</option>', hit = false;
    list.forEach(function (x) { var on = x === cur; if (on) hit = true; h += '<option value="' + esc(x) + '"' + (on ? ' selected' : '') + '>' + esc(x) + '</option>'; });
    if (cur && !hit) h += '<option value="' + esc(cur) + '" selected>⚠ ' + esc(cur) + ' (listede yok)</option>';
    return h;
  }
  function pairEnhance(cityInp, distInp) {
    if (!cityInp || cityInp.getAttribute('data-spx-il')) return;
    cityInp.setAttribute('data-spx-il', '1'); cityInp.style.display = 'none';
    var cs = document.createElement('select'); cs.className = 'spx-ils'; cs.style.cssText = SELST; cityInp.parentNode.insertBefore(cs, cityInp.nextSibling);
    var ds = null;
    if (distInp && !distInp.getAttribute('data-spx-il')) { distInp.setAttribute('data-spx-il', '1'); distInp.style.display = 'none'; ds = document.createElement('select'); ds.className = 'spx-ils'; ds.style.cssText = SELST; distInp.parentNode.insertBefore(ds, distInp.nextSibling); }
    var last = '';
    function sync() {
      if (!document.body.contains(cityInp)) return;
      var cv = cityInp.value, dv = distInp ? distInp.value : '', c = trCity(cv) || cv, d = (distInp && trDist(c, dv)) || dv, sig = cv + '|' + dv;
      if (sig === last && document.activeElement !== cs && document.activeElement !== ds) return; last = sig;
      cs.innerHTML = selOpts(TRK, c, 'İl seçin');
      if (ds) { ds.innerHTML = selOpts(TRD[trCity(c)] || [], d, trCity(c) ? 'İlçe seçin' : 'Önce il seçin'); ds.disabled = !trCity(c) && !d; }
    }
    cs.onchange = function () { setNative(cityInp, cs.value); if (distInp && distInp.value) setNative(distInp, ''); last = ''; setTimeout(sync, 30); };
    if (ds) ds.onchange = function () { setNative(distInp, ds.value); };
    var iv = setInterval(function () { if (!document.body.contains(cityInp)) { clearInterval(iv); cs.remove(); if (ds) ds.remove(); return; } sync(); }, 400); sync();
  }
  function addrEnhance() {
    if (document.body.classList.contains('spx-tech')) return;
    [].forEach.call(document.querySelectorAll('label'), function (lb) {
      var t = (lb.textContent || '').trim(); if (t !== 'Şehir' && t !== 'İl') return;
      var ci = lb.nextElementSibling; if (!ci || ci.tagName !== 'INPUT' || ci.getAttribute('data-spx-il')) return;
      var g = lb.parentElement && lb.parentElement.parentElement, di = null;
      if (g) [].forEach.call(g.children, function (w) { var l2 = w.querySelector && w.querySelector(':scope > label'); if (l2 && (l2.textContent || '').trim() === 'İlçe' && l2.nextElementSibling && l2.nextElementSibling.tagName === 'INPUT') di = l2.nextElementSibling; });
      pairEnhance(ci, di);
    });
    ['mk-gen-city', 'mk-b-city'].forEach(function (k) { var i = document.querySelector('input[data-testid="' + k + '"]'); if (i) pairEnhance(i, null); });
  }
  setInterval(addrEnhance, 600);


  /* ---------- admin: Bayilik Başvuruları → onay penceresinde başvurunun tüm bilgileri ---------- */
  var DLR = { rows: null, techs: null, t: 0, busy: false };
  function dealerInfo() {
    var dlg = document.querySelector('[data-testid="dealer-dialog"]'); if (!dlg) return;
    if ((!DLR.rows || Date.now() - DLR.t > 20000) && !DLR.busy) {
      DLR.busy = true;
      Promise.all([pcall('GET', '/dealers'), pcall('GET', '/technicians').catch(function () { return []; })]).then(function (r) { DLR.rows = r[0] || []; DLR.techs = r[1] || []; DLR.t = Date.now(); }).catch(function () { DLR.rows = DLR.rows || []; }).then(function () { DLR.busy = false; });
      if (!DLR.rows) return;
    }
    if (!DLR.rows) return;
    var title = ((dlg.querySelector('h2') || {}).textContent || '').trim(), tel = dlg.querySelector('a[href^="tel:"]'), ph = tel ? tel.getAttribute('href').slice(4) : '';
    var d = DLR.rows.filter(function (x) { return x.company === title && (!ph || x.phone === ph); })[0] || DLR.rows.filter(function (x) { return x.company === title; })[0]; if (!d) return;
    var sig = d.id + '|' + DLR.t, ex = dlg.querySelector('.spx-di'); if (ex && ex.getAttribute('data-sig') === sig) return; if (ex) ex.remove();
    var city = trCity(d.city) || d.city || '', dl = (d.districts && d.districts.length) ? d.districts : String(d.district || '').split(/[,;]/).map(function (x) { return x.trim(); }).filter(Boolean);
    var gl = (d.service_groups || []).map(function (g) { var t = TGRP.filter(function (x) { return x[0] === g; })[0]; return t ? t[1] : g; });
    var inCity = 0, inDist = 0; (DLR.techs || []).forEach(function (t) { var pf = t.profile || {}; if (pf.city && nrm(pf.city) === nrm(city)) { inCity++; if ((pf.districts || []).some(function (x) { return dl.some(function (y) { return nrm(x) === nrm(y); }); })) inDist++; } });
    var chip = function (t, c) { return '<span style="display:inline-block;background:' + (c || '#eff6ff') + ';color:#0a1f44;border-radius:99px;padding:2px 9px;font-size:12px;font-weight:600;margin:2px 3px 2px 0">' + esc(t) + '</span>'; };
    var row = function (k, v) { return '<div style="padding:8px 10px;background:#f8fafc;border-radius:8px"><div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:#64748b;font-weight:700">' + k + '</div><div style="font-weight:600;margin-top:2px;font-size:13.5px">' + v + '</div></div>'; };
    var box = document.createElement('div'); box.className = 'spx-di'; box.setAttribute('data-sig', sig); box.style.cssText = 'border:1px solid #bfdbfe;background:#f0f7ff;border-radius:10px;padding:12px;margin:2px 0';
    box.innerHTML = '<div style="font-size:12px;font-weight:800;color:#1d4ed8;margin-bottom:8px">📋 BAŞVURUDAKİ TÜM BİLGİLER</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' +
      row('İl', esc(city || '-')) + row('Araç', d.has_vehicle ? 'Var 🚗' : 'Belirtilmemiş / yok') +
      '<div style="grid-column:1/-1">' + row('Hizmet verebildiği ilçeler (' + dl.length + ')', dl.length ? dl.map(function (x) { return chip(x); }).join('') : '-') + '</div>' +
      '<div style="grid-column:1/-1">' + row('İş Ortağı Sözleşmesi / Gizlilik Taahhütnamesi', d.contract && d.contract.accepted ? '<span style="color:#166534">✔ Onaylandı · ' + esc(String(d.contract.at || '').slice(0, 16).replace('T', ' ')) + ' · v' + esc(d.contract.ver || '1') + '</span>' : '<span style="color:#b45309">Kayıt yok (eski başvuru)</span>') + '</div>' +
      '<div style="grid-column:1/-1">' + row('Servis grupları', gl.length ? gl.map(function (x) { return chip(x, '#fff7ed'); }).join('') : esc(d.service_types || '-')) + '</div>' +
      row('Uzman markalar', esc(d.brands || '-')) + row('Deneyim', d.experience_years ? d.experience_years + ' yıl' : '-') +
      row('E-posta', esc(d.email || '-')) + row('Başvuru kaynağı', esc((d.source && (d.source.channel || d.source.label)) || d.channel || '-')) + '</div>' +
      '<div style="margin-top:8px;font-size:12.5px;color:#334155">📊 Bu ilde kayıtlı usta: <b>' + inCity + '</b>' + (dl.length ? ' · bu ilçelerde hizmet veren: <b>' + inDist + '</b>' : '') + (inCity === 0 ? ' — <span style="color:#15803d;font-weight:700">bölgede ihtiyaç olabilir</span>' : '') + '</div>' +
      (d.technician_id ? '' : '<div style="margin-top:6px;font-size:12px;color:#64748b">✔ “Usta hesabı oluştur” dediğinizde il, ilçeler, servis grupları, marka, deneyim, araç ve başvuru notu usta detayına otomatik aktarılır.</div>');
    var g = dlg.querySelector('.grid.grid-cols-2'); if (g) g.insertAdjacentElement('afterend', box); else dlg.appendChild(box);
  }
  setInterval(dealerInfo, 700);

  /* ---------- admin: Servis kayıtları — varsayılan son 15 gün + güçlü filtre (1000+ kayıt için) ---------- */
  var JF = (function () { var d = { scope: '15', from: '', to: '', open: true, city: '', dist: '', type: '', brand: '', q: '' }; try { var v = JSON.parse(LS.get('spx_jf', 'null')); if (v && typeof v === 'object') Object.keys(d).forEach(function (k) { if (v[k] != null) d[k] = v[k]; }); } catch (e) { } d.q = ''; d.shown = null; return d; })();
  window.SPX_JF = JF;
  function jfSave() { try { LS.set('spx_jf', JSON.stringify({ scope: JF.scope, from: JF.from, to: JF.to, open: JF.open, city: JF.city, dist: JF.dist, type: JF.type, brand: JF.brand, q: JF.q })); } catch (e) { } }
  function jfDate(dt) { var m = dt.getMonth() + 1, d = dt.getDate(); return dt.getFullYear() + '-' + (m < 10 ? '0' : '') + m + '-' + (d < 10 ? '0' : '') + d; }
  function jfQs() {
    var a = [], enc = encodeURIComponent;
    if (JF.q) a.push('q=' + enc(JF.q));
    else {
      var now = new Date();
      if (JF.scope === '15' || JF.scope === '7' || JF.scope === '30' || JF.scope === '90') { a.push('days=' + JF.scope); if (!JF.open) a.push('keep_open=false'); }
      else if (JF.scope === 'today') a.push('date_from=' + jfDate(now));
      else if (JF.scope === 'year') a.push('date_from=' + now.getFullYear() + '-01-01');
      else if (JF.scope === 'custom') { if (JF.from) a.push('date_from=' + JF.from); if (JF.to) a.push('date_to=' + JF.to); }
    }
    if (JF.city) a.push('city=' + enc(JF.city)); if (JF.dist) a.push('district=' + enc(JF.dist)); if (JF.type) a.push('device_type=' + enc(JF.type)); if (JF.brand) a.push('brand=' + enc(JF.brand));
    return a.length ? '?' + a.join('&') : '';
  }
  (function () {
    var oo = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (m, u) {
      try {
        if (String(m).toUpperCase() === 'GET' && /\/api\/jobs$/.test(String(u)) && location.pathname.replace(/\/$/, '') === '/admin/jobs' && !document.body.classList.contains('spx-tech')) {
          var a = [].slice.call(arguments); a[1] = String(u) + jfQs(); this.addEventListener('load', function () { try { var j = JSON.parse(this.responseText); if (Array.isArray(j)) JF.shown = j.length; } catch (e) { } });
          return oo.apply(this, a);
        }
      } catch (e) { }
      return oo.apply(this, arguments);
    };
  })();
  var JFM = { d: null, t: 0, busy: false };
  var JTL = { kombi: 'Kombi', klima: 'Klima', buzdolabi: 'Buzdolabı', 'camasir-makinesi': 'Çamaşır makinesi', 'bulasik-makinesi': 'Bulaşık makinesi', televizyon: 'Televizyon', sofben: 'Şofben', firin: 'Fırın', ocak: 'Ocak', diger: 'Diğer' };
  var jfT = 0;
  function jfApply() { jfSave(); clearTimeout(jfT); jfT = setTimeout(function () { var bar = document.getElementById('spx-jf'); if (bar) bar.setAttribute('data-sig', ''); JF.shown = null; goto('/admin/account'); setTimeout(function () { goto('/admin/jobs'); }, 450); }, 200); }
  function jobsFilterBar() {
    var pg = document.querySelector('[data-testid="jobs-page"]'), ex = document.getElementById('spx-jf');
    if (!pg || !/^\/admin\/jobs\/?$/.test(location.pathname) || document.body.classList.contains('spx-tech')) { if (ex) ex.remove(); return; }
    if ((!JFM.d || Date.now() - JFM.t > 60000) && !JFM.busy) { JFM.busy = true; pcall('GET', '/jobs/meta?days=15').then(function (d) { JFM.d = d; JFM.t = Date.now(); }).catch(function () { JFM.d = JFM.d || {}; JFM.t = Date.now(); }).then(function () { JFM.busy = false; }); }
    if (!JFM.d) return;
    var d = JFM.d, nat = document.querySelector('[data-testid="jobs-search"]'), host = nat; while (host && host.parentElement !== pg) host = host.parentElement; if (!host) return;
    var sig = JSON.stringify([JF.scope, JF.from, JF.to, JF.open, JF.city, JF.dist, JF.type, JF.brand, JF.q, d.total, d.recent, d.older, d.old_open]);
    if (!ex || ex.getAttribute('data-sig') !== sig) {
      if (ex) ex.remove();
      var st = 'border:1px solid #cbd5e1;background:#fff;border-radius:8px;padding:6px 9px;font-size:13px;color:#0a1f44;max-width:170px';
      var SC = [['15', 'Son 15 gün'], ['today', 'Bugün'], ['7', 'Son 7 gün'], ['30', 'Son 30 gün'], ['90', 'Son 90 gün'], ['year', 'Bu yıl'], ['all', 'Tümü (tüm kayıtlar)'], ['custom', 'Tarih aralığı seç…']];
      var types = (d.types || []).map(function (t) { return [t, JTL[t] || t]; });
      var def = JF.scope === '15' && !JF.city && !JF.dist && !JF.type && !JF.brand && !JF.q;
      ex = document.createElement('div'); ex.id = 'spx-jf'; ex.setAttribute('data-sig', sig); ex.className = 'notranslate';
      ex.style.cssText = 'border:1px solid #bfdbfe;background:#f0f7ff;border-radius:12px;padding:10px 12px;margin:8px 0 10px;display:flex;flex-direction:column;gap:8px';
      ex.innerHTML = '<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center"><b style="font-size:12px;color:#1d4ed8">📅 KAYIT DÖNEMİ</b>' +
        '<select data-k="scope" style="' + st + '">' + SC.map(function (x) { return '<option value="' + x[0] + '"' + (JF.scope === x[0] ? ' selected' : '') + '>' + x[1] + '</option>'; }).join('') + '</select>' +
        (JF.scope === 'custom' ? '<input type="date" data-k="from" value="' + esc(JF.from) + '" style="' + st + '"> – <input type="date" data-k="to" value="' + esc(JF.to) + '" style="' + st + '"><button data-k="go" style="border:0;background:#0a1f44;color:#fff;border-radius:8px;padding:6px 12px;font-weight:700;font-size:13px;cursor:pointer">Uygula</button>' : '') +
        (/^(15|7|30|90)$/.test(JF.scope) ? '<label style="display:flex;align-items:center;gap:5px;font-size:12.5px;color:#334155"><input type="checkbox" data-k="open"' + (JF.open ? ' checked' : '') + '> Bitmemiş (açık) kayıtlar her zaman görünsün</label>' : '') + '</div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center"><b style="font-size:12px;color:#1d4ed8">🔎 FİLTRE</b>' +
        '<select data-k="city" style="' + st + '">' + selOpts(TRK, JF.city, 'Tüm iller') + '</select>' +
        '<select data-k="dist" style="' + st + '"' + (TRD[JF.city] ? '' : ' disabled') + '>' + selOpts(TRD[JF.city] || [], JF.dist, 'Tüm ilçeler') + '</select>' +
        '<select data-k="type" style="' + st + '">' + selOpts([], '', 'Tüm cihaz türleri').replace('</option>', '</option>' + types.map(function (t) { return '<option value="' + esc(t[0]) + '"' + (JF.type === t[0] ? ' selected' : '') + '>' + esc(t[1]) + '</option>'; }).join('')) + '</select>' +
        '<select data-k="brand" style="' + st + '">' + selOpts(d.brands || [], JF.brand, 'Tüm markalar') + '</select>' +
        '<input data-k="q" value="' + esc(JF.q) + '" placeholder="Kayıt no / ad / telefon / adres (tüm tarihlerde)" style="' + st + ';min-width:240px;max-width:none;flex:1"><button data-k="search" style="border:0;background:#f27a1a;color:#fff;border-radius:8px;padding:7px 14px;font-weight:700;font-size:13px;cursor:pointer">Ara</button>' +
        (def ? '' : '<button data-k="clr" style="border:1px solid #cbd5e1;background:#fff;color:#b91c1c;border-radius:8px;padding:6px 12px;font-weight:700;font-size:13px;cursor:pointer">✕ Sıfırla (son 15 gün)</button>') + '</div>' +
        '<div data-i style="font-size:12.5px;color:#334155"></div>';
      ex.onchange = function (e) { var k = e.target.getAttribute('data-k'); if (!k || k === 'q') return; if (k === 'open') JF.open = e.target.checked; else if (k === 'from' || k === 'to') { JF[k] = e.target.value; return; } else { JF[k] = e.target.value; if (k === 'city') JF.dist = ''; if (k === 'scope') JF.q = ''; } if (k === 'scope' && JF.scope === 'custom') { jfSave(); ex.setAttribute('data-sig', ''); return; } jfApply(); };
      ex.onclick = function (e) { var k = e.target.getAttribute('data-k'); if (k === 'go') jfApply(); else if (k === 'search') { JF.q = ex.querySelector('[data-k=q]').value.trim(); jfApply(); } else if (k === 'clr') { JF.scope = '15'; JF.from = JF.to = JF.city = JF.dist = JF.type = JF.brand = JF.q = ''; JF.open = true; jfApply(); } };
      ex.onkeydown = function (e) { if (e.key === 'Enter' && e.target.getAttribute('data-k') === 'q') { JF.q = e.target.value.trim(); jfApply(); } };
      host.parentElement.insertBefore(ex, host);
    }
    var inf = ex.querySelector('[data-i]'); if (!inf) return;
    var nv = ((nat && nat.value) || '').trim(), parts = [];
    parts.push('Listelenen: <b>' + (JF.shown == null ? '…' : JF.shown) + '</b> kayıt');
    parts.push('Toplam kayıt: <b>' + (d.total || 0) + '</b>');
    if (JF.scope === '15' && !JF.q) parts.push('Son 15 günden eski: <b>' + (d.older || 0) + '</b> kayıt' + (d.old_open ? ' (bunlardan <b style="color:#b45309">' + d.old_open + '</b> tanesi hâlâ açık, listede görünür)' : '') + ' — filtreyle bulabilirsiniz');
    if (JF.q) parts.push('<span style="color:#b45309;font-weight:700">“' + esc(JF.q) + '” için tüm tarihlerde arama</span>');
    var h = parts.join(' · ');
    if (nv.length >= 3 && nv !== JF.q && (JF.scope !== 'all' || JF.city || JF.dist || JF.type || JF.brand)) h += ' <button data-k="deep" style="border:1px solid #f27a1a;background:#fff7ed;color:#c2570c;border-radius:8px;padding:3px 10px;font-weight:700;font-size:12px;cursor:pointer;margin-left:6px">🔎 “' + esc(nv.slice(0, 24)) + '” tüm tarihlerde ara</button>';
    if (inf.getAttribute('data-h') !== h) { inf.setAttribute('data-h', h); inf.innerHTML = h; var db = inf.querySelector('[data-k=deep]'); if (db) db.onclick = function () { JF.q = nv; jfApply(); }; }
  }
  setInterval(jobsFilterBar, 700);
  /* Mobilde filtre bloklari gizli; "Filtrele" butonuna basinca acilir */
  var JT = { open: false };
  (function () {
    var s = document.createElement('style');
    s.textContent = '#spx-jt{display:none}@media(max-width:768px){#spx-jt{display:flex!important}body:not(.spx-fopen) #spx-jf,body:not(.spx-fopen) #spx-jq,body:not(.spx-fopen) .spx-nf{display:none!important}}';
    document.head.appendChild(s);
  })();
  function jobsToggle() {
    var pg = document.querySelector('[data-testid="jobs-page"]'), ex = document.getElementById('spx-jt');
    if (!pg || !/^\/admin\/jobs\/?$/.test(location.pathname) || document.body.classList.contains('spx-tech')) { if (ex) ex.remove(); document.body.classList.remove('spx-fopen'); return; }
    var nat = document.querySelector('[data-testid="jobs-search"]'), host = nat; while (host && host.parentElement !== pg) host = host.parentElement; if (!host) return;
    host.classList.add('spx-nf');
    if (!ex) {
      ex = document.createElement('button'); ex.id = 'spx-jt'; ex.type = 'button'; ex.className = 'notranslate';
      ex.style.cssText = 'width:100%;align-items:center;justify-content:space-between;gap:8px;border:1px solid #bfdbfe;background:#f0f7ff;color:#0a1f44;border-radius:12px;padding:11px 14px;margin:8px 0 10px;font-weight:700;font-size:14px;cursor:pointer;text-align:left';
      ex.onclick = function () { JT.open = !JT.open; jobsToggle(); };
      pg.insertBefore(ex, document.getElementById('spx-jf') || host);
    }
    var jf = document.getElementById('spx-jf');
    if (jf && ex.nextSibling !== jf && ex.nextSibling !== host && jf.previousSibling !== ex) pg.insertBefore(ex, jf);
    var n = 0;
    if (JF.scope && JF.scope !== '15') n++;
    ['city', 'dist', 'type', 'brand', 'q'].forEach(function (k) { if (JF[k]) n++; });
    if (typeof JQ !== 'undefined' && JQ.k && JQ.k !== 'all') n++;
    Array.prototype.forEach.call(host.querySelectorAll('select'), function (x) { if (x.selectedIndex > 0) n++; });
    Array.prototype.forEach.call(host.querySelectorAll('input'), function (x) { if (x.value && x.type !== 'checkbox') n++; });
    var cnt = (JF.shown == null ? '' : JF.shown + ' kayıt');
    var h = '<span>🔎 Filtrele' + (n ? ' <b style="background:#f27a1a;color:#fff;border-radius:99px;padding:1px 8px;font-size:12px;margin-left:4px">' + n + '</b>' : '') + '</span><span style="font-weight:600;font-size:12.5px;color:#334155">' + cnt + ' ' + (JT.open ? '▲' : '▼') + '</span>';
    if (ex.getAttribute('data-h') !== h) { ex.setAttribute('data-h', h); ex.innerHTML = h; }
    document.body.classList.toggle('spx-fopen', JT.open);
    ex.setAttribute('aria-expanded', JT.open ? 'true' : 'false');
  }
  setInterval(jobsToggle, 500);



  /* ---------- admin: usta seçim listelerinde il / ilçe / servis grubuna göre akıllı sıralama ---------- */
  var USEL = { names: null, t: 0, busy: false, cache: {} };
  function fiberOf(el) { for (var k in el) { if (k.indexOf('__reactFiber$') === 0) return el[k]; } return null; }
  function selCtx(el) {
    for (var f = fiberOf(el), n = 0; f && n < 300; f = f.return, n++) {
      for (var h = f.memoizedState, i = 0; h && typeof h === 'object' && i < 40; h = h.next, i++) {
        var s = h.memoizedState; if (!s || typeof s !== 'object' || Array.isArray(s)) continue;
        if ('customer_district' in s || 'customer_city' in s) return { city: s.customer_city || '', district: s.customer_district || '', device_type: s.device_type || '', address: s.customer_address || '', customer_id: s.use_existing_customer ? s.customer_id || '' : '' };
        if (s.job_number && s.id) return { job_id: s.id };
        if ('customer_id' in s && 'assigned_technician_id' in s && !s.id) return { customer_id: s.customer_id || '' };
      }
      var pr = f.memoizedProps; if (pr && pr.job && pr.job.id && pr.job.job_number) return { job_id: pr.job.id };
    }
    return null;
  }
  function selEnhance() {
    if (document.body.classList.contains('spx-tech') || !document.querySelector('[data-spx-own]')) return;
    var lb = document.querySelector('[role="listbox"]'); if (!lb || lb.getAttribute('data-spx-sorted')) return;
    var trg = document.querySelector('[role="combobox"][aria-expanded="true"]'); if (!trg || trg.getAttribute('data-testid') === 'jobs-tech-filter') return;
    var lab = trg.parentElement && trg.parentElement.querySelector('label'); if (!lab || !/usta|teknisyen/i.test(lab.textContent || '')) return;
    var opts = [].slice.call(lb.querySelectorAll('[role="option"]')); if (opts.length < 2) return;
    if (!USEL.names && !USEL.busy) { USEL.busy = true; pcall('GET', '/technicians').then(function (a) { var m = {}; (a || []).forEach(function (x) { m[nrm(x.name)] = x.id; }); USEL.names = m; USEL.t = Date.now(); }).catch(function () { USEL.names = {}; }).then(function () { USEL.busy = false; }); return; }
    if (!USEL.names) return;
    var idOf = function (o) { var t = nrm((o.textContent || '').replace(/\(%.*$/, '').replace(/\s+/g, ' ')); var best = ''; Object.keys(USEL.names).forEach(function (n) { if (t.indexOf(n) === 0 && n.length > best.length) best = n; }); return best ? USEL.names[best] : ''; };
    var ids = opts.map(idOf), hit = ids.filter(Boolean).length; if (hit < 1 || hit < opts.length / 2) return;
    var ctx = selCtx(opts[0]); if (!ctx) return;
    lb.setAttribute('data-spx-sorted', '1');
    var url = ctx.job_id ? '/autoassign/suggest?job_id=' + encodeURIComponent(ctx.job_id) : '/autoassign/preview?' + ['city', 'district', 'device_type', 'address', 'customer_id'].map(function (k) { return k + '=' + encodeURIComponent(ctx[k] || ''); }).join('&');
    pcall('GET', url).then(function (r) {
      var rank = r.ranking || [], pos = {}; rank.forEach(function (x, i) { pos[x.technician_id] = x; x._i = i; });
      var par = opts[0].parentElement; if (!par || !document.body.contains(par)) return;
      par.style.display = 'flex'; par.style.flexDirection = 'column';
      var TL = ['✅ Tam uyumlu — aynı il + ilçe + servis grubu', '📍 İlçesinde', '🔧 Aynı ilde, servis grubu uygun', '📍 Aynı ilde', '🔧 Başka ilde, grubu uygun', 'Diğer ustalar (bölge/grup bilgisi yok veya uyumsuz)'];
      var many = opts.length > 14, rows = [];
      var sb = document.createElement('div'); sb.style.cssText = 'order:-3;padding:4px 2px';
      sb.innerHTML = '<input type="text" placeholder="🔎 Usta, il veya ilçe ara…" style="width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:7px 10px;font-size:13px;outline:none">';
      par.insertBefore(sb, par.firstChild);
      var head = document.createElement('div'); head.style.cssText = 'order:-2;padding:6px 10px;font-size:11px;font-weight:700;color:#475569;background:#f1f5f9;border-radius:6px;margin:2px 2px 4px'; head.textContent = 'İş adresine göre en uygun ustalar üstte (il · ilçe · servis grubu · yük)'; par.insertBefore(head, sb.nextSibling);
      var tierFirst = {}, tierCnt = {};
      opts.forEach(function (o, k) {
        var x = pos[ids[k]], row = { o: o, x: x, hay: nrm(o.textContent + ' ' + (x ? x.place : '')) };
        rows.push(row);
        if (!x) { o.style.order = '9000'; row.tier = 9; return; }
        row.tier = x.eligible ? x.tier : 8; o.style.order = String(x._i * 10);
        tierCnt[row.tier] = (tierCnt[row.tier] || 0) + 1; if (tierFirst[row.tier] == null) tierFirst[row.tier] = x._i;
        var tags = []; if (x.city_hit) tags.push('📍 aynı il'); if (x.district_hit && x.city_hit) tags.push('✔ ilçesinde'); if (x.skill_hit) tags.push('🔧 grubu uygun'); tags.push('yük ' + x.load + '/' + x.cap); if (x.has_vehicle) tags.push('🚗');
        if (!x.eligible) o.style.opacity = '.55';
        o.style.flexWrap = 'wrap';
        var pl = document.createElement('div'); pl.style.cssText = 'flex-basis:100%;font-size:11.5px;margin-top:1px;font-weight:700;color:#0a1f44'; pl.textContent = x.place ? '📌 ' + x.place : '📌 il/ilçe girilmemiş'; if (!x.place) pl.style.color = '#b45309'; o.appendChild(pl);
        var b = document.createElement('div'); b.style.cssText = 'flex-basis:100%;font-size:11px;margin-top:1px;color:' + (x.tier === 0 ? '#15803d' : '#64748b'); b.textContent = tags.join(' · ') + (x.eligible ? '' : ' · ' + (x.reasons || []).filter(function (t) { return /dışında|farklı|müsait|limit|aynı saatte|uzman değil/.test(t); }).join(', ')); o.appendChild(b);
        if (x.warn && x.warn.length) { var w = document.createElement('div'); w.style.cssText = 'flex-basis:100%;font-size:11px;font-weight:700;color:#b91c1c'; w.textContent = '⚠ ' + x.warn.map(function (t) { return t === 'il' ? 'farklı ilde' : t === 'ilçe' ? 'ilçe dışında' : 'servis grubu uyumsuz'; }).join(', '); o.appendChild(w); }
      });
      var hdrs = [], hid = [];
      Object.keys(tierFirst).forEach(function (t) {
        var h = document.createElement('div'); h.style.cssText = 'padding:5px 10px;font-size:11px;font-weight:800;color:#0a1f44;background:#e8edf6;border-radius:6px;margin:6px 2px 2px'; h.setAttribute('data-spx-h', t);
        h.style.order = String(t === '8' ? 7999 : tierFirst[t] * 10 - 5);
        h.textContent = (t === '8' ? '⛔ Şu an uygun olmayanlar (müsait değil / limit / çakışma)' : TL[+t]) + ' · ' + tierCnt[t];
        par.appendChild(h); hdrs.push(h);
      });
      var collapse = many ? rows.filter(function (r) { return r.tier >= 4 && r.tier !== 9; }) : [];
      var tg = null, shown = false;
      if (collapse.length) {
        tg = document.createElement('button'); tg.type = 'button'; tg.style.cssText = 'order:7990;margin:6px 2px;border:1px dashed #94a3b8;background:#fff;border-radius:8px;padding:6px;font-size:12px;font-weight:700;color:#1d4ed8;cursor:pointer';
        var apply = function () { collapse.forEach(function (r) { r.o.style.display = shown ? '' : 'none'; }); hdrs.forEach(function (h) { var t = +h.getAttribute('data-spx-h'); if (t >= 4 && t !== 8) h.style.display = shown ? '' : 'none'; }); tg.textContent = shown ? '▾ Diğer bölgelerdeki ustaları gizle' : '▸ Diğer bölgelerdeki ' + collapse.length + ' ustayı göster'; };
        tg.onclick = function (e) { e.preventDefault(); e.stopPropagation(); shown = !shown; apply(); }; tg.onpointerup = function (e) { e.stopPropagation(); };
        apply(); par.appendChild(tg);
      }
      var inp = sb.firstChild;
      ['keydown', 'keyup', 'keypress', 'pointerdown', 'pointerup', 'click'].forEach(function (ev) { inp.addEventListener(ev, function (e) { e.stopPropagation(); }); });
      inp.addEventListener('input', function () {
        var q = nrm(inp.value);
        rows.forEach(function (r) { r.o.style.display = (q && r.hay.indexOf(q) < 0) ? 'none' : (!q && collapse.indexOf(r) >= 0 && !shown ? 'none' : ''); });
        hdrs.forEach(function (h) { h.style.display = q ? 'none' : ''; }); if (tg) tg.style.display = q ? 'none' : '';
        if (!q && tg) { var t0 = shown; shown = t0; hdrs.forEach(function (h) { var t = +h.getAttribute('data-spx-h'); if (t >= 4 && t !== 8 && !shown) h.style.display = 'none'; }); }
      });
      // yanlış atamaya karşı onay: farklı il / uyumsuz servis grubu
      var guard = function (e) {
        var o = e.target.closest && e.target.closest('[role="option"]'); if (!o) return;
        var r = rows.filter(function (z) { return z.o === o; })[0]; if (!r || !r.x || !r.x.warn || !r.x.warn.length || r.x.warn.indexOf('ilçe') >= 0 && r.x.warn.length === 1) return;
        var m = r.x.warn.filter(function (t) { return t !== 'ilçe'; }).map(function (t) { return t === 'il' ? 'farklı ilde çalışıyor (' + (r.x.city || '-') + ')' : 'bu servis grubunda kayıtlı değil'; }).join(' ve ');
        var now = Date.now(), ok; if (now - gT < 900) ok = gOk; else { ok = window.confirm(r.x.name + ' ' + m + '.\n\nYine de bu ustaya atansın mı?'); gT = Date.now(); gOk = ok; }
        if (!ok) { e.stopPropagation(); e.preventDefault(); }
      };
      var gT = 0, gOk = false;
      lb.addEventListener('pointerup', guard, true); lb.addEventListener('click', guard, true);
      setTimeout(function () { try { inp.focus({ preventScroll: true }); } catch (e) { } }, 50);
    }).catch(function () { lb.removeAttribute('data-spx-sorted'); });
  }
  setInterval(selEnhance, 350);

  /* ---------- admin: Teknisyenler → borca göre sırala / sadece borçlular ---------- */
  var TQ = { sort: false, only: false, bal: null, busy: false, t: 0 };
  function techQuick() {
    var pg = document.querySelector('[data-testid="technicians-page"]'), ex = document.getElementById('spx-tq');
    if (!pg || !/^\/admin\/technicians\/?$/.test(location.pathname)) { if (ex) ex.remove(); TQ.sort = false; TQ.only = false; return; }
    if ((!TQ.bal || Date.now() - TQ.t > 30000) && !TQ.busy) { TQ.busy = true; pcall('GET', '/cash/summary').then(function (r) { var m = {}; (r.technician_balances || []).forEach(function (x) { m[x.id] = x.balance || 0; }); TQ.bal = m; TQ.t = Date.now(); }).catch(function () { TQ.bal = TQ.bal || {}; TQ.t = Date.now(); }).then(function () { TQ.busy = false; }); }
    if (!ex) {
      var s = document.querySelector('[data-testid="tech-search"]'), row = s && s.closest('.flex-wrap');
      if (!row) { var c1 = document.querySelector('[data-testid="technicians-page"] [data-testid^="tech-card-"]'); row = c1 && c1.parentElement && c1.parentElement.previousElementSibling; if (row && row.id === 'spx-tf2') row = row.previousElementSibling; }
      ex = document.createElement('span'); ex.id = 'spx-tq'; ex.style.cssText = 'display:inline-flex;gap:8px';
      ex.innerHTML = '<button data-q="sort" style="border:1px solid #cbd5e1;background:#fff;color:#0a1f44;border-radius:8px;padding:5px 12px;font-weight:600;font-size:13px;cursor:pointer">↓ Borca göre sırala</button><button data-q="only" style="border:1px solid #cbd5e1;background:#fff;color:#0a1f44;border-radius:8px;padding:5px 12px;font-weight:600;font-size:13px;cursor:pointer">Sadece borçlular</button>';
      ex.onclick = function (e) { var b = e.target.closest('button[data-q]'); if (!b) return; TQ[b.getAttribute('data-q')] = !TQ[b.getAttribute('data-q')]; techQuick(); };
      if (row) row.appendChild(ex); else ex.setAttribute('data-detached', '1');
    }
    Array.prototype.forEach.call(ex.querySelectorAll('button'), function (b) { var on = TQ[b.getAttribute('data-q')]; b.style.background = on ? '#0a1f44' : '#fff'; b.style.color = on ? '#fff' : '#0a1f44'; });
    Array.prototype.forEach.call(document.querySelectorAll('[data-testid^="tech-card-"]'), function (c) {
      var id = c.getAttribute('data-testid').slice(10), bal = (TQ.bal && TQ.bal[id]) || 0, ord = TQ.sort ? String(-Math.round(bal)) : '', dsp = ((TQ.only && TQ.bal && bal <= 0.5) || !techFilterHit(id)) ? 'none' : '';
      if (c.style.order !== ord) c.style.order = ord; if (c.style.display !== dsp) c.style.display = dsp;
    });
  }
  setInterval(techQuick, 800);

  var GI = {'Servis': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z"/></svg>','Ustalar': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5c2.2.6 3.5 2.4 3.5 5.5"/></svg>','Muhasebe': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="3" width="16" height="18" rx="1"/><path d="M8 7h8M8 12h2M14 12h2M8 16h2M14 16h2"/></svg>','Mağaza & Satış': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 8h14l-1 12H6zM9 8V6a3 3 0 0 1 6 0v2"/></svg>','Web Sitesi': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/></svg>','Pazarlama & İletişim': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11v3l12 5V6zM15 9c2.5.5 4 1.5 4 3s-1.5 2.5-4 3M7 15l1.5 5"/></svg>','Yönetim': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 3v6c0 4.5-3.2 7.8-8 9-4.8-1.2-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg>'};
  var MSCR = {};
  document.addEventListener('scroll', function (e) { var n = e.target; if (n && n.tagName === 'NAV' && n.closest && n.closest('aside')) MSCR[n.closest('.fixed') ? 'm' : 'd'] = n.scrollTop; }, true);
  function badgeOf(a) { var b = a && a.querySelector('[data-testid^="badge-"]'); return b ? b.textContent.trim() : ''; }
  function tick() {
    var asides = document.querySelectorAll('aside nav'); if (!asides.length) return;
    Array.prototype.forEach.call(asides, function (nav) {
      var nl = nativeLinks(nav), sig = Object.keys(nl).join('|') + '#' + (me().admin_role || '') + (me().perms || []).join(','), own = nav.querySelector(':scope > [data-spx-own]');
      if (own && own.getAttribute('data-sig') === sig) { Array.prototype.forEach.call(own.querySelectorAll('a.spx-it'), function (a) { var k = a.getAttribute('data-k') || 'ek:', bd = a.querySelector('.spx-bd:not(.spx-od)'), t = k === 'ek:onay' ? (window.__onayN ? String(window.__onayN) : '') : k.indexOf('ek:') === 0 ? '' : (badgeOf(nl[k]) || (ADMB && ADMB[k] ? (k === '/admin/governance' ? '!' : String(ADMB[k])) : '')); if (t && t !== '0') { if (!bd) { bd = document.createElement('span'); bd.className = 'spx-bd'; a.appendChild(bd); } bd.textContent = t; } else if (bd) bd.remove(); var od = a.querySelector('.spx-od'), ov2 = k === '/admin/jobs' && ADMB && (ADMB.jobs_overdue > 0 || ADMB.call_overdue > 0) ? (ADMB.jobs_overdue || 0) + (ADMB.call_overdue || 0) : 0; if (ov2) { if (!od) { od = document.createElement('span'); od.className = 'spx-bd spx-od'; od.style.background = '#f59e0b'; od.style.marginLeft = '4px'; od.title = 'Randevu saati geçmiş iş'; a.appendChild(od); } od.textContent = ov2 + ' ⏰'; } else if (od) od.remove(); }); markActive(); return; }
      var sKey = nav.closest('.fixed') ? 'm' : 'd', sTop = nav.scrollTop || MSCR[sKey] || 0;
      if (own) own.remove();
      Array.prototype.forEach.call(nav.children, function (c) { c.style.display = 'none'; });
      own = document.createElement('div'); own.setAttribute('data-spx-own', '1'); own.setAttribute('data-sig', sig);
      var rl = ''; try { rl = (JSON.parse(LS.get('user', '{}')) || {}).admin_role || ''; } catch (e) { }
      var h = '';
      MENU.forEach(function (g) {
        var items = g[1].filter(function (it) { return canMenu(it[0]) && (it[0].indexOf('ek:') === 0 || !!nl[it[0]]); });
        if (!items.length) return;
        if (g[0]) h += '<div class="spx-gt">' + (GI[g[0]] || '') + '<span class="l">' + esc(g[0]) + '</span></div>';
        items.forEach(function (it) {
          var ek = it[0].indexOf('ek:') === 0, ico = ek ? IC[it[2]] : (nl[it[0]].querySelector('svg') ? nl[it[0]].querySelector('svg').outerHTML : '');
          h += '<div><a class="spx-it" data-k="' + it[0] + '" href="' + (ek ? '#' : it[0]) + '">' + ico + '<span class="l">' + esc(it[1]) + '</span></a>';
          if (SUB[it[0]]) h += '<div class="spx-sub" data-for="' + it[0] + '" style="display:none">' + SUB[it[0]].map(function (s) { return '<a href="' + it[0] + '?tab=' + s[0] + '" data-t="' + s[0] + '" data-p="' + it[0] + '">' + esc(s[1]) + '</a>'; }).join('') + '</div>';
          h += '</div>';
        });
      });
      h += '<div class="spx-gt">' + IC.moon + '<span class="l">Görünüm</span></div><div><a class="spx-it" href="#" data-theme="1">' + IC.moon + '<span class="l" id="spx-thl">Koyu / açık tema</span></a></div>';
      own.innerHTML = h;
      own.onclick = function (e) {
        var s = e.target.closest('.spx-sub a'); var a = e.target.closest('a.spx-it');
        if (s) { e.preventDefault(); if (ov) ov.classList.remove('on'); goto(s.getAttribute('href')); closeMobile(); setTimeout(markActive, 50); return; }
        if (!a) return; e.preventDefault();
        if (a.hasAttribute('data-theme')) { setTheme(!root.classList.contains('spx-dark')); return; }
        var k = a.getAttribute('data-k');
        if (k.indexOf('ek:') === 0) { open(k.slice(3)); closeMobile(); markActive(); return; }
        if (ov) ov.classList.remove('on');
        var n = nl[k]; if (n) n.click(); else goto(k); setTimeout(markActive, 50);
      };
      try { if (typeof MG !== 'undefined' && MG) menuAccOne(own, false); } catch (e) { }   /* kapali/acik durumu eklemeden once uygula: bir an hepsi acik gorunmesin */
      nav.appendChild(own); markActive(); nav.scrollTop = sTop; requestAnimationFrame(function () { if (nav.scrollTop !== sTop) nav.scrollTop = sTop; }); document.documentElement.classList.add('spx-menu-on');
    });
    btn.style.display = document.querySelector('aside') ? 'none' : 'block';
  }
  /* ================= ATÖLYE (usta + admin) ================= */
  var ATL_ST = { atolyede: ['Atölyede', '#d97706'], hazir: ['Hazır', '#16a34a'], teslim: ['Teslim edildi', '#64748b'] };
  var ATL_FMT = [['a4', '🖨 A4 yazıcı / PDF'], ['t80', 'Termal 80 mm'], ['t58', 'Termal 58 mm'], ['nokta', 'Nokta vuruşlu']];
  function atlUrl(tok, fmt) { return location.origin + '/atolye/' + tok + '?fmt=' + fmt; }
  function atlBtns(tok) { return ATL_FMT.map(function (f) { return '<a href="' + atlUrl(tok, f[0]) + '" target="_blank" rel="noopener" style="display:inline-block;margin:3px 4px 3px 0;border:1px solid #cbd5e1;background:#fff;color:#0a1f44;border-radius:8px;padding:8px 11px;font-weight:700;font-size:13px;text-decoration:none">' + f[1] + '</a>'; }).join(''); }
  function atlSig(canvas) {
    var ctx = canvas.getContext('2d'), dr = false, any = false; ctx.lineWidth = 2.4; ctx.lineCap = 'round'; ctx.strokeStyle = '#111';
    function pt(e) { var r = canvas.getBoundingClientRect(); return [(e.clientX - r.left) * canvas.width / r.width, (e.clientY - r.top) * canvas.height / r.height]; }
    canvas.style.touchAction = 'none';
    canvas.addEventListener('pointerdown', function (e) { dr = true; any = true; var p = pt(e); ctx.beginPath(); ctx.moveTo(p[0], p[1]); try { canvas.setPointerCapture(e.pointerId); } catch (x) { } e.preventDefault(); });
    canvas.addEventListener('pointermove', function (e) { if (!dr) return; var p = pt(e); ctx.lineTo(p[0], p[1]); ctx.stroke(); e.preventDefault(); });
    ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (n) { canvas.addEventListener(n, function () { dr = false; }); });
    return { clear: function () { ctx.clearRect(0, 0, canvas.width, canvas.height); any = false; }, data: function () { return any ? canvas.toDataURL('image/png') : ''; } };
  }
  var ATLCARD = {}, ATLBUSY = false;
  function atlCompress(file) {
    return new Promise(function (res, rej) {
      var fr = new FileReader(); fr.onerror = function () { rej(new Error('Fotoğraf okunamadı')); };
      fr.onload = function () { var im = new Image(); im.onerror = function () { rej(new Error('Fotoğraf açılamadı')); }; im.onload = function () { var k = Math.min(1, 1000 / Math.max(im.width, im.height)), c = document.createElement('canvas'); c.width = Math.round(im.width * k); c.height = Math.round(im.height * k); c.getContext('2d').drawImage(im, 0, 0, c.width, c.height); res(c.toDataURL('image/jpeg', 0.72)); }; im.src = fr.result; };
      fr.readAsDataURL(file);
    });
  }
  function atlModal(jid, reasons, done, job) {
    var m = document.createElement('div'); m.id = 'spx-atlm'; m.className = 'notranslate';
    m.style.cssText = 'position:fixed;inset:0;z-index:100000;background:rgba(10,31,68,.55);overflow:auto;padding:10px';
    var I = 'width:100%;border:1px solid #cbd5e1;border-radius:8px;padding:9px;font-size:15px;box-sizing:border-box;margin:4px 0 10px;background:#fff;color:#111';
    var S = 'font-size:14px;font-weight:800;color:#0a1f44;margin:12px 0 6px';
    var acc = ['Adaptör', 'Kumanda', 'Kablo', 'Batarya', 'Çanta/kutu', 'Filtre'];
    var L = 'font-size:13px;font-weight:700;color:#0f172a';
    var SG = function (id, cl, t) { return '<div style="flex:1;min-width:0"><label style="' + L + '">' + t + ' *</label><canvas id="' + id + '" width="600" height="260" style="width:100%;height:130px;border:1.5px dashed #94a3b8;border-radius:10px;background:#fafafa;margin-top:4px;touch-action:none"></canvas><div style="text-align:right"><button id="' + cl + '" type="button" style="border:0;background:none;color:#1155cc;font-size:13px">İmzayı sil</button></div></div>'; };
    m.innerHTML = '<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:14px;padding:16px;color:#0f172a" id="atlb"><div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:18px">🔧 Cihazı atölyeye al</b><button id="atl_x" style="border:0;background:#f1f5f9;border-radius:8px;padding:6px 12px;font-size:15px">✕</button></div>' +
      '<div style="font-size:13px;color:#64748b;margin:6px 0 10px">Bilgileri müşteriyle birlikte doldurun, müşteri ve teknisyen imzalasın; “Teslim alma formu” oluşur.</div>' +
      (job ? '<div style="background:#f1f5f9;border-radius:10px;padding:9px 11px;margin-bottom:12px;font-size:14px"><b>' + esc(job.customer || '') + '</b>' + (job.phone ? ' · ' + esc(job.phone) : '') + '<br><span style="color:#475569">' + esc(job.device || '') + '</span></div>' : '') +
      '<label style="' + L + '">Atölyeye alınma nedeni *</label><select id="atl_r" style="' + I + '"><option value="">Seçin…</option>' + reasons.map(function (r) { return '<option>' + esc(r) + '</option>'; }).join('') + '</select>' +
      '<label style="' + L + '">Cihazın dış durumu</label><input id="atl_c" style="' + I + '" placeholder="Örn: çizik yok, kapak kırık, çalışmıyor">' +
      '<label style="' + L + '">Mevcut hasar / not</label><input id="atl_d" style="' + I + '" placeholder="Varsa belirtin">' +
      '<label style="' + L + '">Birlikte alınan aksesuarlar</label><div style="margin:4px 0 6px">' + acc.map(function (x) { return '<label style="display:inline-block;margin:0 10px 6px 0;font-size:14px"><input type="checkbox" class="atl_a" value="' + x + '"> ' + x + '</label>'; }).join('') + '</div><input id="atl_a2" style="' + I + '" placeholder="Diğer aksesuar">' +
      '<div style="display:flex;gap:8px"><div style="flex:1"><label style="' + L + '">Tahmini teslim</label><input id="atl_e" style="' + I + '" placeholder="Örn: 3 gün"></div><div style="flex:1"><label style="' + L + '">Tahmini ücret (₺)</label><input id="atl_p" inputmode="decimal" style="' + I + '"></div></div>' +
      '<label style="' + L + '">Cihaz fotoğrafları * <span style="font-weight:400;color:#64748b">(en az 1)</span></label><div id="atl_ph" style="display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 12px"><label style="width:84px;height:84px;border:2px dashed #f27a1a;border-radius:10px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:12px;color:#c2410c;cursor:pointer;font-weight:700"><span style="font-size:28px">📷</span>Fotoğraf çek<input id="atl_pf" type="file" accept="image/*" capture="environment" multiple style="display:none"></label></div>' +
      '<div style="display:flex;gap:10px">' + SG('atl_s', 'atl_sc', 'Müşteri imzası') + SG('atl_s2', 'atl_sc2', 'Teknisyen imzası') + '</div>' +
      '<label style="display:flex;gap:8px;align-items:flex-start;font-size:14px;margin:8px 0 12px"><input type="checkbox" id="atl_k" style="margin-top:3px"> <span>Müşteri, cihazın onarım amacıyla atölyeye alınmasını ve form şartlarını kabul etti.</span></label>' +
      '<button id="atl_ok" style="width:100%;background:#f27a1a;color:#fff;border:0;border-radius:10px;padding:13px;font-size:16px;font-weight:800">Atölyeye al ve formu oluştur</button><div id="atl_msg" style="color:#dc2626;font-size:13px;margin-top:8px"></div></div>';
    document.body.appendChild(m);
    var sg = atlSig(m.querySelector('#atl_s')), sg2 = atlSig(m.querySelector('#atl_s2')), PH = [], REASON = '', q = function (s) { return m.querySelector(s); };
    q('#atl_r').onchange = function () { REASON = this.value; };
    var phDraw = function () { Array.prototype.forEach.call(m.querySelectorAll('.atl_th'), function (x) { x.remove(); }); PH.forEach(function (d, i) { var w = document.createElement('div'); w.className = 'atl_th'; w.style.cssText = 'position:relative;width:84px;height:84px'; w.innerHTML = '<img src="' + d + '" style="width:84px;height:84px;object-fit:cover;border-radius:10px"><button data-i="' + i + '" style="position:absolute;top:-6px;right:-6px;width:22px;height:22px;border-radius:50%;border:0;background:#dc2626;color:#fff;font-size:13px">✕</button>'; q('#atl_ph').insertBefore(w, q('#atl_ph').lastElementChild); }); };
    q('#atl_ph').onclick = function (e) { var b = e.target.closest('button[data-i]'); if (b) { PH.splice(+b.getAttribute('data-i'), 1); phDraw(); } };
    q('#atl_pf').onchange = function () { var fs = Array.prototype.slice.call(this.files || [], 0, 6 - PH.length); this.value = ''; q('#atl_msg').textContent = 'Fotoğraf hazırlanıyor…'; Promise.all(fs.map(atlCompress)).then(function (a) { PH = PH.concat(a).slice(0, 6); phDraw(); q('#atl_msg').textContent = ''; }).catch(function (er) { q('#atl_msg').textContent = er.message; }); };
    q('#atl_x').onclick = function () { m.remove(); }; q('#atl_sc').onclick = sg.clear; q('#atl_sc2').onclick = sg2.clear;
    q('#atl_ok').onclick = function () {
      var b = q('#atl_ok'), acs = Array.prototype.map.call(m.querySelectorAll('.atl_a:checked'), function (x) { return x.value; }); if (q('#atl_a2').value.trim()) acs.push(q('#atl_a2').value.trim());
      var er = function (t) { q('#atl_msg').textContent = t; };
      if (!REASON) return er('Atölyeye alma nedenini seçin.'); if (!PH.length) return er('En az bir cihaz fotoğrafı ekleyin.'); if (!sg.data()) return er('Müşteri imzası gerekli.'); if (!sg2.data()) return er('Teknisyen imzası gerekli.'); if (!q('#atl_k').checked) return er('Müşteri onay kutusu işaretlenmeli.');
      b.disabled = true; b.textContent = 'Kaydediliyor…';
      pcall('POST', '/workshop/' + jid + '/intake', { reason: REASON, condition: q('#atl_c').value, damage: q('#atl_d').value, accessories: acs.join(', '), est_ready: q('#atl_e').value, price_estimate: q('#atl_p').value, signature: sg.data(), tech_signature: sg2.data(), photos: PH, consent: true })
        .then(function (r) { q('#atlb').innerHTML = '<div style="text-align:center;padding:6px"><div style="font-size:38px">✅</div><b style="font-size:18px">Atölyeye alındı</b><div style="font-size:15px;margin:6px 0 12px">Fiş no: <b>' + esc(r.receipt_no) + '</b></div><a href="' + atlUrl(r.token, 'a4') + '" target="_blank" rel="noopener" style="display:block;background:#f27a1a;color:#fff;border-radius:10px;padding:14px;font-size:16px;font-weight:800;text-decoration:none;margin-bottom:10px">📄 Müşteri formunu aç / PDF</a><div style="font-size:12px;color:#64748b;margin-bottom:4px">Başka yazıcı ile yazdırmak için:</div><div>' + atlBtns(r.token) + '</div><button id="atl_d2" style="margin-top:12px;width:100%;border:0;background:#0a1f44;color:#fff;border-radius:10px;padding:12px;font-size:15px;font-weight:700">Tamam</button></div>'; q('#atl_d2').onclick = function () { m.remove(); done(); }; })
        .catch(function (e2) { b.disabled = false; b.textContent = 'Atölyeye al ve formu oluştur'; er(e2.message || 'Hata'); });
    };
  }
  function atlJobCard() {
    if (!document.body.classList.contains('spx-tech')) return;
    var mt = location.pathname.match(/^\/tech\/jobs\/([^\/?#]+)/), ex = document.getElementById('spx-atl');
    if (!mt) { if (ex) ex.remove(); return; }
    var jid = mt[1], mn = document.querySelector('main'); if (!mn) return;
    if (ex && ex.getAttribute('data-j') !== jid) { ex.remove(); ex = null; }
    var c = ATLCARD[jid];
    if (!c || Date.now() - c.t > (c.d && c.d.workshop ? 60000 : 8000)) {
      if (!ATLBUSY) { ATLBUSY = true; pcall('GET', '/workshop/' + jid).then(function (r) { ATLCARD[jid] = { t: Date.now(), d: r }; }).catch(function () { ATLCARD[jid] = { t: Date.now() - 45000, d: null }; }).then(function () { ATLBUSY = false; if (ex) ex.remove(); }); }
      if (!c) return;
    }
    var bt = document.getElementById('spx-atl-btn');
    if (bt && bt.getAttribute('data-j') !== jid) { bt.remove(); bt = null; }
    if (!c.d) return;
    var w = c.d.workshop, st = c.d.job && c.d.job.status;
    /* yalnız usta müşteride işe başladıktan sonra; "Müşteri Vazgeçti" butonunun hemen üstünde, o butonlar gibi, metinsiz */
    if (!w && st === 'basladi') {
      var cb = document.querySelector('[data-testid=tech-cancel-button]');
      if (cb && !bt) {
        bt = cb.cloneNode(true); bt.id = 'spx-atl-btn'; bt.setAttribute('data-j', jid); bt.removeAttribute('data-testid'); bt.removeAttribute('disabled');
        bt.className = (cb.className || '').replace(/text-rose-\d+/g, 'text-orange-600').replace(/border-rose-\d+/g, 'border-orange-300').replace(/hover:bg-rose-\d+/g, 'hover:bg-orange-50');
        bt.style.setProperty('margin-bottom', '8px'); bt.style.setProperty('color', '#c2410c'); bt.style.setProperty('border-color', '#fdba74');
        bt.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px;display:inline-block;vertical-align:-3px"><path d="M14.7 6.3a4 4 0 0 0-5.2 5.2L3 18l3 3 6.5-6.5a4 4 0 0 0 5.2-5.2l-2.6 2.6-2.4-.6-.6-2.4z"/></svg>Atölyeye Al';
        bt.onclick = function (e) { e.preventDefault(); e.stopPropagation(); atlModal(jid, c.d.reasons || [], function () { delete ATLCARD[jid]; ATLLIST = null; var x = document.getElementById('spx-atl-btn'); if (x) x.remove(); }, c.d.job); };
        cb.parentNode.insertBefore(bt, cb);
      }
    } else if (bt) { bt.remove(); }
    if (!w) { if (ex) ex.remove(); return; }
    if (ex) return;
    var h = '<div id="spx-atl" data-j="' + esc(jid) + '" class="notranslate" style="background:#fff;border:1px solid #fdba74;border-radius:14px;padding:14px;margin-bottom:12px">';
    {
      var s = ATL_ST[w.state] || ['', '#64748b'];
      h += '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><div><div style="font-weight:800;color:#0a1f44">🔧 Atölye kaydı · ' + esc(w.receipt_no) + '</div><div style="font-size:12px;color:#64748b">' + DT(w.taken_at) + ' · ' + esc(w.reason || '') + ' · ' + w.days + ' gün</div></div><span style="background:' + s[1] + ';color:#fff;border-radius:20px;padding:4px 11px;font-size:12px;font-weight:700;white-space:nowrap">' + s[0] + '</span></div><div style="margin-top:8px">' + atlBtns(w.token) + '</div>';
      if (w.state === 'atolyede') h += '<button data-a="hazir" style="margin-top:6px;width:100%;background:#16a34a;color:#fff;border:0;border-radius:10px;padding:11px;font-size:15px;font-weight:700">Onarım bitti — cihaz hazır</button>';
      if (w.state === 'hazir') h += '<button data-a="teslim" style="margin-top:6px;width:100%;background:#0a1f44;color:#fff;border:0;border-radius:10px;padding:11px;font-size:15px;font-weight:700">Müşteriye teslim edildi</button>';
    }
    h += '</div>'; mn.insertAdjacentHTML('afterbegin', h);
    document.getElementById('spx-atl').onclick = function (e) {
      var b = e.target.closest('button[data-a]'); if (!b) return; var a = b.getAttribute('data-a');
      if (a === 'take') { atlModal(jid, c.d.reasons || [], function () { delete ATLCARD[jid]; ATLLIST = null; var x = document.getElementById('spx-atl'); if (x) x.remove(); }); return; }
      if (!confirm(a === 'hazir' ? 'Cihaz hazır olarak işaretlensin mi? Yönetime bildirim gider.' : 'Cihaz müşteriye teslim edildi olarak kaydedilsin mi?')) return;
      b.disabled = true; pcall('POST', '/workshop/' + jid + '/state', { state: a }).then(function () { delete ATLCARD[jid]; ATLLIST = null; var x = document.getElementById('spx-atl'); if (x) x.remove(); toast('Kaydedildi'); }).catch(function (er) { b.disabled = false; toast(er.message); });
    };
  }
  setInterval(atlJobCard, 700);
  var ATLLIST = null, ATLLBUSY = false, ATLON = false;
  function atlRowsHtml(rows) {
    if (!rows.length) return '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:36px 12px;text-align:center;color:#64748b;font-size:14px">Atölyede cihaz yok</div>';
    return rows.map(function (r) {
      var s = ATL_ST[r.state] || ['', '#64748b'];
      return '<div data-r="' + esc(r.id) + '" style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:12px;margin-bottom:10px"><div style="display:flex;justify-content:space-between;gap:8px"><div><b style="font-size:15px">' + esc(r.customer || '') + '</b><div style="font-size:12px;color:#64748b">' + esc(r.device) + ' · ' + esc(r.receipt_no) + '</div><div style="font-size:12px;color:#64748b">' + esc(r.reason || '') + '</div></div><div style="text-align:right"><span style="background:' + s[1] + ';color:#fff;border-radius:20px;padding:3px 10px;font-size:12px;font-weight:700;white-space:nowrap">' + s[0] + '</span><div style="font-size:12px;color:' + (r.late ? '#dc2626' : '#64748b') + '">' + r.days + ' gündür' + (r.late ? ' ⚠' : '') + '</div></div></div>' +
        '<div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap"><a href="' + atlUrl(r.token, 'a4') + '" target="_blank" rel="noopener" style="border:1px solid #cbd5e1;border-radius:8px;padding:7px 11px;font-size:13px;font-weight:700;color:#0a1f44;text-decoration:none">Form / Yazdır</a><a href="/tech/jobs/' + esc(r.id) + '" style="border:1px solid #cbd5e1;border-radius:8px;padding:7px 11px;font-size:13px;font-weight:700;color:#0a1f44;text-decoration:none">Kaydı aç</a>' + (r.state === 'atolyede' ? '<button data-s="hazir" style="border:0;background:#16a34a;color:#fff;border-radius:8px;padding:7px 11px;font-size:13px;font-weight:700">Hazır</button>' : '<button data-s="teslim" style="border:0;background:#0a1f44;color:#fff;border-radius:8px;padding:7px 11px;font-size:13px;font-weight:700">Teslim edildi</button>') + '</div></div>';
    }).join('');
  }
  function atlPaneFill() {
    var pn = document.getElementById('spx-atl-pane'); if (!pn) return;
    pn.innerHTML = atlRowsHtml((ATLLIST && ATLLIST.d.rows) || []);
  }
  function atlTabOff() {
    var tb = document.getElementById('spx-atl-tab'), pn = document.getElementById('spx-atl-pane'); ATLON = false;
    if (pn) pn.style.display = 'none';
    if (tb) { tb.setAttribute('data-state', 'inactive'); tb.setAttribute('aria-selected', 'false'); }
    var tl = document.querySelector('[role=tablist]'); if (!tl) return;
    Array.prototype.forEach.call(tl.querySelectorAll('[role=tab]:not(#spx-atl-tab)'), function (t) { if (t._spxSt) { t.setAttribute('data-state', t._spxSt); t.setAttribute('aria-selected', t._spxSt === 'active' ? 'true' : 'false'); } });
    Array.prototype.forEach.call(tl.parentElement.querySelectorAll('[role=tabpanel]'), function (x) { x.style.removeProperty('display'); });
  }
  function atlTabOn() {
    var tb = document.getElementById('spx-atl-tab'), tl = document.querySelector('[role=tablist]'); if (!tb || !tl) return; ATLON = true;
    Array.prototype.forEach.call(tl.querySelectorAll('[role=tab]:not(#spx-atl-tab)'), function (t) { t._spxSt = t.getAttribute('data-state'); t.setAttribute('data-state', 'inactive'); t.setAttribute('aria-selected', 'false'); });
    tb.setAttribute('data-state', 'active'); tb.setAttribute('aria-selected', 'true');
    Array.prototype.forEach.call(tl.parentElement.querySelectorAll('[role=tabpanel]:not(#spx-atl-pane)'), function (x) { x.style.setProperty('display', 'none', 'important'); });
    var pn = document.getElementById('spx-atl-pane'); if (!pn) { pn = document.createElement('div'); pn.id = 'spx-atl-pane'; pn.className = 'notranslate'; pn.style.marginTop = '16px'; tl.parentElement.appendChild(pn);
      pn.onclick = function (e) {
        var b = e.target.closest('button[data-s]'); if (!b) return; var id = b.closest('[data-r]').getAttribute('data-r'), st = b.getAttribute('data-s');
        if (!confirm(st === 'hazir' ? 'Cihaz hazır olarak işaretlensin mi? Yönetime bildirim gider.' : 'Teslim edildi olarak kaydedilsin mi?')) return;
        b.disabled = true; pcall('POST', '/workshop/' + id + '/state', { state: st }).then(function () { delete ATLCARD[id]; return pcall('GET', '/workshop'); }).then(function (r) { ATLLIST = { t: Date.now(), d: r }; atlPaneFill(); toast('Kaydedildi'); }).catch(function (er) { b.disabled = false; toast(er.message); });
      }; }
    pn.style.display = ''; atlPaneFill();
    pcall('GET', '/workshop').then(function (r) { ATLLIST = { t: Date.now(), d: r }; if (ATLON) atlPaneFill(); }).catch(function () { });
  }
  function atlHomeCard() {
    var tb = document.getElementById('spx-atl-tab'), pn = document.getElementById('spx-atl-pane');
    var on = document.body.classList.contains('spx-tech') && /^\/tech\/?$/.test(location.pathname), tl = on ? document.querySelector('[role=tablist]') : null;
    var ok = tl && Array.prototype.some.call(tl.querySelectorAll('[role=tab]'), function (t) { return /Aktif/.test(t.textContent); });
    if (!ok) { if (tb) tb.remove(); if (pn) pn.remove(); ATLON = false; return; }
    if (!tb) {
      var tabs = tl.querySelectorAll('[role=tab]'), src = tabs[tabs.length - 1]; if (!src) return;
      tb = src.cloneNode(true); tb.id = 'spx-atl-tab'; tb.removeAttribute('aria-controls'); tb.removeAttribute('id'); tb.id = 'spx-atl-tab'; tb.setAttribute('data-state', 'inactive'); tb.setAttribute('aria-selected', 'false'); tb.setAttribute('type', 'button'); tb.textContent = 'Atölye (0)';
      tb.onclick = function (e) { e.preventDefault(); e.stopPropagation(); atlTabOn(); };
      tl.appendChild(tb); tl.style.gridTemplateColumns = 'repeat(3, minmax(0, 1fr))';
      tl.addEventListener('click', function (e) { var t = e.target.closest('[role=tab]'); if (t && t.id !== 'spx-atl-tab' && ATLON) atlTabOff(); }, true);
      tl.addEventListener('pointerdown', function (e) { var t = e.target.closest('[role=tab]'); if (t && t.id !== 'spx-atl-tab' && ATLON) atlTabOff(); }, true);
    }
    if (!ATLLIST || Date.now() - ATLLIST.t > 45000) {
      if (!ATLLBUSY) { ATLLBUSY = true; pcall('GET', '/workshop').then(function (r) { ATLLIST = { t: Date.now(), d: r }; if (ATLON) atlPaneFill(); }).catch(function () { ATLLIST = ATLLIST || { t: Date.now() - 30000, d: { rows: [] } }; }).then(function () { ATLLBUSY = false; }); }
    }
    if (ATLLIST) { var n = (ATLLIST.d.rows || []).length, tx = 'Atölye (' + n + ')'; if (tb.textContent !== tx) tb.textContent = tx; }
    if (ATLLIST) {
      var ws = {}, hid = 0; (ATLLIST.d.rows || []).forEach(function (r) { if (r.state === 'atolyede' || r.state === 'hazir') { ws[r.id] = 1; if (/^(atandi|yolda|basladi)$/.test(r.job_status || '')) hid++; } });
      var aktif = Array.prototype.filter.call(tl.querySelectorAll('[role=tab]:not(#spx-atl-tab)'), function (t) { return /Aktif/.test(t.textContent); })[0];
      Array.prototype.forEach.call(document.querySelectorAll('a[data-testid^="tech-job-"]'), function (a) { var id = (a.getAttribute('data-testid') || '').slice(9); var hide = !!ws[id] && aktif && aktif.getAttribute('data-state') === 'active' && !ATLON; if (hide) a.style.setProperty('display', 'none', 'important'); else if (a._spxHid) a.style.removeProperty('display'); a._spxHid = hide; });
      if (aktif) { var w = document.createTreeWalker(aktif, NodeFilter.SHOW_TEXT), nd, tn = null; while ((nd = w.nextNode())) { if (/^\d+$/.test(nd.nodeValue.trim())) tn = nd; }
        if (tn) { if (tn._spxSet === undefined || tn.nodeValue !== String(tn._spxSet)) tn._spxRaw = parseInt(tn.nodeValue, 10); var v = String(Math.max(0, tn._spxRaw - hid)); if (tn.nodeValue !== v) tn.nodeValue = v; tn._spxSet = v; } }
    }
  }
  setInterval(atlHomeCard, 800);

  var ATFIL = 'aktif';
  function drawAtolye() {
    var q = ATFIL === 'teslim' ? '?state=teslim' : '';
    call('GET', '/workshop' + q).then(function (d) {
      var rows = d.rows.filter(function (r) { return ATFIL === 'aktif' || ATFIL === 'teslim' || r.state === ATFIL; });
      var h = '<div class="spx-card"><div class="spx-g"><label>Liste<select id="atf">' + [['aktif', 'Atölyede + Hazır'], ['atolyede', 'Sadece atölyede'], ['hazir', 'Sadece hazır'], ['teslim', 'Teslim edilenler (60 gün)']].map(function (x) { return '<option value="' + x[0] + '"' + (x[0] === ATFIL ? ' selected' : '') + '>' + x[1] + '</option>'; }).join('') + '</select></label></div><small style="color:#64748b;display:block;margin-top:6px">Ustalar “Cihazı atölyeye al” dediğinde kayıt buraya düşer ve size bildirim gider. 7 gün ve üstü bekleyenler “geciken” sayılır.</small></div>' +
        grid([stat('Atölyede', d.counts.atolyede || 0), stat('Hazır (teslim bekliyor)', d.counts.hazir || 0), stat('Geciken (7+ gün)', '<span style="color:' + (d.counts.late ? '#dc2626' : 'inherit') + '">' + (d.counts.late || 0) + '</span>')]) +
        '<div class="spx-card">' + (rows.length ? tbl(['Fiş', 'Müşteri', 'Cihaz', 'Usta', 'Alınma', 'Gün', 'Neden', 'Durum'], rows.map(function (r) { var s = ATL_ST[r.state] || ['', '']; return tr_(['<b>' + esc(r.receipt_no) + '</b><small>' + esc(r.job_number || '') + '</small>', esc(r.customer || '') + '<small>' + esc(r.phone || '') + '</small>', esc(r.device), esc(r.tech), DT(r.taken_at), '<b style="color:' + (r.late ? '#dc2626' : 'inherit') + '">' + r.days + '</b>', esc(r.reason || ''), pill(s[0], s[1])], 'data-k="' + esc(r.id) + '"'); })) : '<div style="color:#64748b;padding:8px">Kayıt yok.</div>') + '</div>';
      body().innerHTML = h; $('#atf').onchange = function () { ATFIL = this.value; drawAtolye(); };
      body().onclick = function (e) { var t = e.target.closest('tr[data-k]'); if (t) atolyeDetail(t.getAttribute('data-k')); };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  function atolyeDetail(id) {
    body().innerHTML = 'Yükleniyor…';
    call('GET', '/workshop/' + id).then(function (d) {
      var r = d.workshop; if (!r) return drawAtolye(); var s = ATL_ST[r.state] || ['', ''];
      var kv = function (k, v) { return '<div class="spx-row"><div class="t"><small>' + k + '</small>' + (esc(v || '') || '—') + '</div></div>'; };
      var h = '<div style="margin-bottom:10px"><button class="spx-b" id="ab">← Listeye dön</button></div><div class="spx-card"><b style="font-size:18px">' + esc(r.receipt_no) + '</b> ' + pill(s[0], s[1]) + ' <small style="display:inline">· ' + r.days + ' gündür atölyede' + (r.late ? ' ⚠ geciken' : '') + '</small></div>' +
        '<div class="spx-card"><div class="spx-g" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr))"><div>' + kv('Müşteri', r.customer) + kv('Telefon', r.phone) + kv('Adres', r.address) + '</div><div>' + kv('Cihaz', r.device) + kv('Seri no', r.serial) + kv('Müşteri beyanı (arıza)', r.fault) + '</div><div>' + kv('Alınma nedeni', r.reason) + kv('Cihaz durumu', r.condition) + kv('Hasar / not', r.damage) + kv('Aksesuarlar', r.accessories) + '</div><div>' + kv('Alan usta', r.tech) + kv('Alınma tarihi', r.taken_at ? new Date(r.taken_at).toLocaleString('tr-TR') : '') + kv('Tahmini teslim', r.est_ready) + kv('Tahmini ücret', r.price_estimate ? r.price_estimate + ' ₺' : '') + kv('Müşteri imzası', r.has_signature ? 'Alındı ✔' : 'Alınmadı') + kv('Teknisyen imzası', r.has_tech_signature ? 'Alındı ✔' : 'Alınmadı') + kv('Fotoğraf', (r.photo_count || 0) + ' adet') + '</div></div></div>' +
        '<div class="spx-card" id="atl_pics"><b>Fotoğraflar ve imzalar</b><div id="atl_pics_b" style="margin-top:8px;color:#64748b">Yükleniyor…</div></div>' +
        '<div class="spx-card"><b>Yazdır / PDF</b><div style="margin-top:6px">' + atlBtns(r.token) + '</div><small style="color:#64748b">A4: yazıcıdan veya “PDF indir”. Termal ve nokta vuruşlu çıktılar sayfa içinden yazdırılır.</small></div>' +
        '<div class="spx-card"><b>Durum</b><div style="margin:8px 0">' + (r.state === 'atolyede' ? '<button class="spx-b p" data-s="hazir">Hazır işaretle</button> ' : '') + (r.state === 'hazir' ? '<button class="spx-b p" data-s="teslim">Teslim edildi</button> <button class="spx-b" data-s="atolyede">Atölyeye geri al</button>' : '') + '</div>' +
        '<div class="spx-g"><label style="grid-column:span 2">Not ekle<input id="an_t"></label></div><button class="spx-b" id="an_a" style="margin-top:6px">Notu kaydet</button></div>' +
        '<div class="spx-card"><b>Geçmiş</b>' + (r.history || []).slice().reverse().map(function (x) { var s2 = ATL_ST[x.state] || ['', '']; return '<div class="spx-row"><div class="t">' + pill(s2[0], s2[1]) + ' ' + esc(x.note || '') + '<small>' + esc(x.by || '') + ' · ' + (x.at ? new Date(x.at).toLocaleString('tr-TR') : '') + '</small></div></div>'; }).join('') + '</div>';
      body().innerHTML = h; $('#ab').onclick = drawAtolye; body().onclick = null;
      call('GET', '/workshop/' + id + '/photos').then(function (pp) { var x = $('#atl_pics_b'); if (!x) return; x.style.color = ''; x.innerHTML = '<div style="display:flex;gap:8px;flex-wrap:wrap">' + (pp.photos || []).map(function (u) { return '<a href="' + u + '" target="_blank"><img src="' + u + '" style="height:110px;border-radius:8px;border:1px solid #e2e8f0"></a>'; }).join('') + '</div><div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:10px">' + [['Müşteri imzası', pp.signature], ['Teknisyen imzası', pp.tech_signature], ['Teslim imzası', pp.delivery_signature]].filter(function (z) { return z[1]; }).map(function (z) { return '<div><small>' + z[0] + '</small><br><img src="' + z[1] + '" style="height:60px;background:#fff;border:1px solid #e2e8f0;border-radius:6px"></div>'; }).join('') + '</div>'; }).catch(function () { var x = $('#atl_pics_b'); if (x) x.textContent = 'Yüklenemedi'; });
      Array.prototype.forEach.call(body().querySelectorAll('button[data-s]'), function (b) { b.onclick = function () { call('POST', '/workshop/' + id + '/state', { state: b.getAttribute('data-s') }).then(function () { atolyeDetail(id); }).catch(fail); }; });
      $('#an_a').onclick = function () { var x = $('#an_t').value.trim(); if (!x) return; call('POST', '/workshop/' + id + '/note', { note: x }).then(function () { atolyeDetail(id); }).catch(fail); };
    }).catch(function (e) { fail(e); drawAtolye(); });
  }

  /* ================= CANLI ZİYARETÇİLER ================= */
  var LIVET = null, LIVEOPEN = {}, LIVEERR = 0, LIVEMODE = 'live';
  var CTR = { call_click: '📞 Aradı', whatsapp_click: '💬 WhatsApp', form_submit: '📝 Form' };
  function ago(s) { s = +s || 0; return s < 60 ? s + ' sn' : s < 3600 ? Math.floor(s / 60) + ' dk' : Math.floor(s / 3600) + ' sa'; }
  function liveCard(s, hist) {
          var open = LIVEOPEN[s.id], hot = s.conv_call || s.conv_whatsapp || s.conv_form;
          var dot = '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:' + (s.online && !hist ? '#16a34a' : '#94a3b8') + ';' + (s.online && !hist ? 'box-shadow:0 0 0 4px rgba(22,163,74,.2)' : '') + '"></span>';
          var h = '<div class="spx-card" data-v="' + esc(s.id) + '" style="cursor:pointer;margin-bottom:8px;' + (hot ? 'border-color:#16a34a;background:#f0fdf4' : '') + (s.online || hist ? '' : ';opacity:.7') + '"><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' + dot + ' <b>' + esc(s.channel_label) + '</b>' + (s.source_name ? '<small style="display:inline">· ' + esc(s.source_name) + '</small>' : '') + ' ' + pill(s.device || '—') + ' <small style="display:inline">' + esc(s.browser || '') + ' ' + esc(s.os || '') + '</small>' +
            (hot ? ' ' + pill('📞 İletişime geçti', '#16a34a') : '') + (s.searches.length ? ' ' + pill('🔎 Arama yaptı', '#7c3aed') : '') + '<span style="margin-left:auto;font-size:12px;color:#64748b">' + (hist ? (s.first_seen ? new Date(s.first_seen).toLocaleString('tr-TR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '') : (s.online ? 'şu an' : ago(s.idle_sec) + ' önce')) + ' · sitede ' + ago(s.duration_sec) + ' · ' + s.pages_count + ' sayfa</span></div>' +
            '<div style="margin-top:6px;font-size:14px">📍 <b>' + esc(s.current_page || '/') + '</b>' + (s.current_title ? ' <small style="display:inline">' + esc(s.current_title) + '</small>' : '') + '</div>' +
            (s.term ? '<div style="font-size:13px;margin-top:3px">🔑 Reklam kelimesi: <b>' + esc(s.term) + '</b>' + (s.campaign ? ' <small style="display:inline">(' + esc(s.campaign) + ')</small>' : '') + '</div>' : '') +
            (s.searches.length ? '<div style="font-size:13px;margin-top:3px">🔎 Site içi arama: ' + s.searches.map(function (x) { return '<b>' + esc(x.q) + '</b>'; }).join(', ') + '</div>' : '');
          if (open) h += '<div style="margin-top:8px;border-top:1px dashed #cbd5e1;padding-top:8px;font-size:13px"><div><b>Gezdiği sayfalar:</b></div>' + s.path.map(function (p) { return '<div>' + (p.ts ? new Date(p.ts).toLocaleTimeString('tr-TR') : '') + ' — ' + esc(p.path) + (p.title ? ' <small style="display:inline">' + esc(p.title) + '</small>' : '') + '</div>'; }).join('') +
            (s.events.length ? '<div style="margin-top:6px"><b>Eylemler:</b> ' + s.events.map(function (x) { return esc(CTR[x.type] || x.type) + ' (' + (x.ts ? new Date(x.ts).toLocaleTimeString('tr-TR') : '') + ')'; }).join(', ') + '</div>' : '') +
            '<div style="margin-top:6px;color:#64748b">İlk giriş: ' + esc(s.landing_page || '') + ' · Geliş: ' + esc(s.referrer || 'doğrudan') + ' · Ekran: ' + esc(s.screen || '—') + ' · IP: ' + esc(s.ip || '—') + (s.city ? ' · ' + esc(s.city) : '') + '</div></div>';
          return h + '</div>';
        }

  /* ---- Canlı > Geçmiş: tarih aralığı + filtre ile ziyaretçi hareketleri ---- */
  var HF = { p: 'today', frm: '', to: '', channel: '', device: '', action: '', q: '', city: '', skip: 0 };
  function liveToggle(cur) {
    var bt = function (k, t) { return '<button class="spx-b' + (cur === k ? ' p' : '') + '" data-lm="' + k + '">' + t + '</button>'; };
    return '<div style="display:flex;gap:6px;margin-bottom:10px">' + bt('live', '🟢 Canlı') + bt('hist', '🕘 Geçmiş hareketler') + '</div>';
  }
  function pad2(n) { return (n < 10 ? '0' : '') + n; }
  function ymd(d) { return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); }
  function histRange() {
    var t = new Date(), d = function (n) { var x = new Date(t); x.setDate(x.getDate() - n); return ymd(x); };
    if (HF.p === 'today') return [d(0), d(0)]; if (HF.p === 'yday') return [d(1), d(1)]; if (HF.p === '7') return [d(6), d(0)];
    if (HF.p === '30') return [d(29), d(0)]; if (HF.p === '90') return [d(89), d(0)];
    return [HF.frm || d(0), HF.to || HF.frm || d(0)];
  }
  function drawHist() {
    var b = body(), box;
    b.innerHTML = liveToggle('hist') + '<div class="spx-card"><div class="spx-g" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">' +
      '<label>Tarih<select id="hf_p"><option value="today">Bugün</option><option value="yday">Dün</option><option value="7">Son 7 gün</option><option value="30">Son 30 gün</option><option value="90">Son 90 gün</option><option value="x">Özel aralık…</option></select></label>' +
      '<label class="hf_x">Başlangıç<input type="date" id="hf_f"></label><label class="hf_x">Bitiş<input type="date" id="hf_t"></label>' +
      '<label>Kaynak<select id="hf_c"><option value="">Hepsi</option></select></label>' +
      '<label>Cihaz<select id="hf_d"><option value="">Hepsi</option><option value="mobil">Mobil</option><option value="masaustu">Masaüstü</option><option value="tablet">Tablet</option></select></label>' +
      '<label>Ne yaptı?<select id="hf_a"><option value="">Hepsi</option><option value="any">İletişime geçenler</option><option value="call">Arayanlar</option><option value="whatsapp">WhatsApp yazanlar</option><option value="form">Form dolduranlar</option><option value="search">Site içi arama yapanlar</option><option value="none">Hiçbir şey yapmadan çıkanlar</option></select></label>' +
      '<label>Sayfa / kelime<input id="hf_q" placeholder="örn. samsung, kombi, /markalar"></label><label>Şehir<input id="hf_city" placeholder="örn. Ankara"></label></div>' +
      '<div style="margin-top:8px"><button class="spx-b p" id="hf_go">Filtrele</button> <button class="spx-b" id="hf_rs">Temizle</button> <button class="spx-b" id="hf_csv">CSV indir</button></div></div><div id="hf_out"></div>';
    box = document.getElementById('hf_out');
    var $$ = function (i) { return document.getElementById(i); };
    $$('hf_p').value = HF.p; $$('hf_f').value = HF.frm; $$('hf_t').value = HF.to; $$('hf_d').value = HF.device; $$('hf_a').value = HF.action; $$('hf_q').value = HF.q; $$('hf_city').value = HF.city;
    function xvis() { [].forEach.call(b.querySelectorAll('.hf_x'), function (l) { l.style.display = $$('hf_p').value === 'x' ? '' : 'none'; }); }
    xvis(); $$('hf_p').onchange = xvis;
    function qs(skip, lim) {
      var r = histRange();
      return '/visitors/history?frm=' + r[0] + '&to=' + r[1] + '&channel=' + encodeURIComponent(HF.channel) + '&device=' + encodeURIComponent(HF.device) + '&action=' + HF.action + '&q=' + encodeURIComponent(HF.q) + '&city=' + encodeURIComponent(HF.city) + '&skip=' + skip + '&limit=' + (lim || 40);
    }
    function read() { HF.p = $$('hf_p').value; HF.frm = $$('hf_f').value; HF.to = $$('hf_t').value; HF.channel = $$('hf_c').value; HF.device = $$('hf_d').value; HF.action = $$('hf_a').value; HF.q = $$('hf_q').value.trim(); HF.city = $$('hf_city').value.trim(); HF.skip = 0; }
    var shown = [];
    function run(more) {
      if (!more) { shown = []; HF.skip = 0; box.innerHTML = '<div class="spx-card" style="color:#64748b">Yükleniyor…</div>'; }
      call('GET', qs(HF.skip)).then(function (d) {
        var cs = $$('hf_c'); if (cs && cs.options.length < 2) { d.channels.forEach(function (c) { var o = document.createElement('option'); o.value = c.v; o.textContent = c.k; cs.appendChild(o); }); cs.value = HF.channel; }
        shown = shown.concat(d.sessions); HF.skip = shown.length;
        var rate = d.total ? Math.round(d.contacted * 1000 / d.total) / 10 : 0;
        var h = grid([stat('Oturum', d.total), stat('İletişime geçen', '<span style="color:#16a34a">' + d.contacted + '</span>', '%' + rate + ' dönüşüm'), stat('Site içi arama yapan', d.searched), stat('Ort. süre', ago(d.avg_duration)), stat('Ort. sayfa', d.avg_pages)]);
        h += '<div class="spx-card"><b>Kaynağa göre</b><div style="margin-top:4px">' + (d.by_channel.length ? d.by_channel.map(function (x) { return '<span class="spx-pill" style="margin:2px 4px 2px 0;cursor:pointer" data-ch="' + esc(x.v) + '">' + esc(x.k) + ' · <b>' + x.n + '</b></span>'; }).join('') : '<small>—</small>') + '</div></div>';
        h += shown.length ? shown.map(function (x) { return liveCard(x, true); }).join('') : '<div class="spx-card" style="color:#64748b">Bu filtreyle oturum bulunamadı.</div>';
        if (shown.length < d.total) h += '<div style="text-align:center;margin:10px 0"><button class="spx-b" id="hf_more">Daha fazla göster (' + (d.total - shown.length) + ' kaldı)</button></div>';
        box.innerHTML = h;
        var mb = $$('hf_more'); if (mb) mb.onclick = function () { run(true); };
      }).catch(function (e) { box.innerHTML = '<div class="spx-card">Geçmiş alınamadı: ' + esc(e.message) + '</div>'; });
    }
    $$('hf_go').onclick = function () { read(); run(false); };
    $$('hf_rs').onclick = function () { HF = { p: 'today', frm: '', to: '', channel: '', device: '', action: '', q: '', city: '', skip: 0 }; drawHist(); };
    $$('hf_q').onkeydown = $$('hf_city').onkeydown = function (e) { if (e.key === 'Enter') { read(); run(false); } };
    $$('hf_csv').onclick = function () {
      read(); call('GET', qs(0, 100)).then(function (d) {
        var rows = [['Tarih', 'Kaynak', 'Reklam kelimesi', 'Cihaz', 'Şehir', 'İlk sayfa', 'Sayfa sayısı', 'Süre (sn)', 'Aradı', 'WhatsApp', 'Form', 'Site içi arama', 'Gezdiği sayfalar']].concat(d.sessions.map(function (s) {
          return [s.first_seen ? new Date(s.first_seen).toLocaleString('tr-TR') : '', s.channel_label, s.term, s.device, s.city, s.landing_page, s.pages_count, s.duration_sec, s.conv_call, s.conv_whatsapp, s.conv_form, s.searches.map(function (x) { return x.q; }).join(' | '), s.path.map(function (x) { return x.path; }).join(' > ')];
        }));
        dl('ziyaretciler-' + histRange()[0] + '.csv', rows.map(function (r) { return r.map(function (c) { return '"' + String(c == null ? '' : c).replace(/"/g, '""') + '"'; }).join(';'); }).join('\n'));
        toast('İlk ' + d.sessions.length + ' oturum indirildi');
      }).catch(fail);
    };
    b.onclick = function (e) {
      var lm = e.target.closest('[data-lm]'); if (lm) { LIVEMODE = lm.getAttribute('data-lm'); drawCanli(); return; }
      var ch = e.target.closest('[data-ch]'); if (ch) { $$('hf_c').value = ch.getAttribute('data-ch'); read(); run(false); return; }
      var c = e.target.closest('[data-v]'); if (!c) return; var k = c.getAttribute('data-v'); LIVEOPEN[k] = !LIVEOPEN[k];
      var s = shown.filter(function (x) { return x.id === k; })[0]; if (s) { var nw = document.createElement('div'); nw.innerHTML = liveCard(s, true); c.replaceWith(nw.firstChild); }
    };
    run(false);
  }
  function drawCanli() {
    if (LIVEMODE === 'hist') { if (LIVET) { clearInterval(LIVET); LIVET = null; } return drawHist(); }
    if (LIVET) { clearInterval(LIVET); LIVET = null; }
    var first = true;
    function tick() {
      if (TAB !== 'canli' || !ov || !ov.classList.contains('on')) { clearInterval(LIVET); LIVET = null; return; }
      call('GET', '/visitors/live').then(function (d) {
        if (TAB !== 'canli') return; LIVEERR = 0;
        var on = d.sessions.filter(function (s) { return s.online; }), off = d.sessions.filter(function (s) { return !s.online; });
        var chips = function (arr) { return arr.length ? arr.map(function (x) { return '<span class="spx-pill" style="margin:2px 4px 2px 0">' + esc(x.k) + ' · <b>' + x.n + '</b></span>'; }).join('') : '<small>—</small>'; };
        var card = function (x) { return liveCard(x, false); };
        var html = liveToggle('live') + '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px"><span style="width:10px;height:10px;border-radius:50%;background:#16a34a;display:inline-block"></span><b>Canlı</b> <small style="display:inline;color:#64748b">5 saniyede bir yenilenir · son güncelleme ' + new Date().toLocaleTimeString('tr-TR') + '</small></div>' +
          grid([stat('Şu an sitede', '<span style="color:#16a34a">' + d.online + '</span>'), stat('Arama yapan', d.online_searching), stat('Arayan / yazan', d.online_called), stat('Bugün oturum', d.today.sessions), stat('Bugün sayfa görüntüleme', d.today.pageviews), stat('Bugün arama yapan', d.today.call_sessions)]) +
          '<div class="spx-card"><div class="spx-g" style="grid-template-columns:repeat(auto-fit,minmax(220px,1fr))"><div><b>Kaynak</b><div>' + chips(d.by_channel) + '</div></div><div><b>Cihaz</b><div>' + chips(d.by_device) + '</div></div><div><b>Baktıkları sayfalar</b><div>' + chips(d.by_page) + '</div></div></div></div>' +
          '<b>Şu an sitedekiler (' + on.length + ')</b><div style="margin-top:8px">' + (on.length ? on.map(card).join('') : '<div class="spx-card" style="color:#64748b">Şu an sitede kimse yok.</div>') + '</div>' +
          (off.length ? '<b style="display:block;margin-top:14px">Son 30 dakikada ayrılanlar (' + off.length + ')</b><div style="margin-top:8px">' + off.map(card).join('') + '</div>' : '');
        var b = body(), sc = b.scrollTop; b.innerHTML = html; b.scrollTop = sc;
        b.onclick = function (e) { var lm = e.target.closest('[data-lm]'); if (lm) { LIVEMODE = lm.getAttribute('data-lm'); drawCanli(); return; } var c = e.target.closest('[data-v]'); if (!c) return; var k = c.getAttribute('data-v'); LIVEOPEN[k] = !LIVEOPEN[k]; tick(); };
      }).catch(function (e) { LIVEERR++; if (first || LIVEERR > 2) body().innerHTML = '<div class="spx-card">Canlı veri alınamadı: ' + esc(e.message) + ' <small>— otomatik denenecek.</small></div>'; }).then(function () { first = false; });
    }
    tick(); LIVET = setInterval(tick, 5000);
  }

  /* ================= CİHAZ TİPİ GENİŞLETME (servis kaydı / cihaz ekleme: yalnız Kombi-Klima-Diğer çıkıyordu) ================= */
  var XT = [['buzdolabi', 'Buzdolabı'], ['camasir', 'Çamaşır makinesi'], ['bulasik', 'Bulaşık makinesi'], ['kurutma', 'Kurutma makinesi'], ['firin', 'Fırın / Ocak'], ['ankastre', 'Ankastre'], ['derin_dondurucu', 'Derin dondurucu'], ['tv', 'Televizyon'], ['sofben', 'Şofben / Termosifon'], ['davlumbaz', 'Davlumbaz']];
  window.SPX_TIP_VER = 21;
  var SPX_DT = null, SPX_TR = null, SPX_BUSY = false;
  (function () {
    var o = XMLHttpRequest.prototype.open, sd = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function (m, u) { this._spx = [String(m).toUpperCase(), String(u || '')]; return o.apply(this, arguments); };
    XMLHttpRequest.prototype.send = function (b) {
      try {
        if (SPX_DT && this._spx && this._spx[0] === 'POST' && typeof b === 'string') {
          var u = this._spx[1].split('?')[0], j = null;
          if (/\/jobs\/quick$/.test(u)) { j = JSON.parse(b); if (j.device_type === 'diger') { j.device_type = SPX_DT; b = JSON.stringify(j); SPX_DT = null; } }
          else if (/\/customers\/[^\/]+\/devices$/.test(u)) { j = JSON.parse(b); if (j.type === 'diger') { j.type = SPX_DT; b = JSON.stringify(j); SPX_DT = null; } }
        }
      } catch (e) { }
      return sd.call(this, b);
    };
  })();
  function setTrigText(trig, txt) { if (!trig) return; var sp = trig.querySelector('span'); if (!sp) return; var w = document.createTreeWalker(sp, NodeFilter.SHOW_TEXT), n = w.nextNode(); if (n) n.nodeValue = txt; }
  function typeExtend() {
    var lbs = document.querySelectorAll('[role=listbox]');
    Array.prototype.forEach.call(lbs, function (lb) {
      if (lb.querySelector('[data-spx-t]')) return;
      var ops = Array.prototype.slice.call(lb.querySelectorAll('[role=option]'));
      var tx = ops.map(function (x) { return (x.textContent || '').trim(); }).join('|');
      if (ops.length !== 3 || !/^Kombi/.test(tx) || !/Klima/.test(tx) || !/Diğer$/.test(tx)) return;
      var dg = ops[2], trig = lb.id ? document.querySelector('[aria-controls="' + lb.id + '"]') : null;
      XT.forEach(function (t) {
        var c = dg.cloneNode(true); ['data-state', 'aria-selected', 'data-highlighted', 'id'].forEach(function (a) { c.removeAttribute(a); });
        c.setAttribute('data-spx-t', t[0]); c.setAttribute('data-value', t[0]);
        var tn = c.querySelector('[id]') || c; var walker = document.createTreeWalker(c, NodeFilter.SHOW_TEXT), n, done = false; while ((n = walker.nextNode())) { if (!done && n.nodeValue.trim()) { n.nodeValue = t[1]; done = true; } else if (done) n.nodeValue = ''; }
        var pick = function (e) {
          e.preventDefault(); e.stopPropagation(); SPX_BUSY = true; SPX_TR = trig;
          var fire = function (ty) { dg.dispatchEvent(new PointerEvent(ty, { bubbles: true, cancelable: true, pointerType: 'mouse', isPrimary: true })); };
          fire('pointerdown'); fire('pointerup'); dg.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); SPX_BUSY = false; SPX_DT = t[0];
          setTimeout(function () { setTrigText(trig, t[1]); }, 60); setTimeout(function () { setTrigText(trig, t[1]); }, 300);
        };
        c.addEventListener('pointerup', pick, true); c.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); }, true); c.addEventListener('pointerdown', function (e) { e.stopPropagation(); }, true);
        dg.parentNode.appendChild(c);
      });
      ops.forEach(function (x) { x.addEventListener('pointerup', function () { if (SPX_BUSY) return; SPX_DT = null; var tt = (x.textContent || '').trim(); setTimeout(function () { setTrigText(trig, tt); }, 60); }, true); });
    });
  }
  setInterval(typeExtend, 250);

  /* ===== Kurulum/montaj işinde "Tamamla" için "Sonra" fotoğrafı zorunlu ===== */
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-testid=tech-complete-button]'); if (!b || b._spxOk) return;
    var m = location.pathname.match(/^\/tech\/jobs\/([^\/?#]+)/); if (!m) return;
    e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
    var go = function () { b._spxOk = true; try { b.click(); } finally { setTimeout(function () { b._spxOk = false; }, 400); } };
    pcall('GET', '/jobs/' + m[1]).then(function (job) {
      var txt = [job.fault_description, job.work_done, job.notes, job.service_type, job.title].join(' ').toLowerCase();
      var isK = /kurulum|montaj/.test(txt);
      var lab = Array.prototype.filter.call(document.querySelectorAll('main div'), function (d) { return (d.textContent || '').trim() === 'Sonra' && !d.children.length; })[0];
      var n = lab && lab.parentElement ? lab.parentElement.querySelectorAll('img').length : 0;
      if (isK && !n && !(job.photos_after || []).length) { toast('Kurulum işini tamamlamak için "Sonra" bölümüne en az bir fotoğraf ekleyin'); return; }
      go();
    }).catch(go);
  }, true);

  /* ================= WHATSAPP / BİLDİRİM AYARLARI ================= */
  function drawWa() {
    Promise.all([call('GET', '/governance/notify-settings'), call('GET', '/governance/outbox').catch(function () { return []; }), call('GET', '/governance/notify-diagnose').catch(function () { return null; })]).then(function (a) {
      var dg = a[2], c = a[0], ob = (a[1] || []).slice(0, 12), t = c.technician || {}, cu = c.customer || {}, tw = c.twilio || {}, vm = c.verimor || {}, wh = c.webhook || {}, dsm = c.daily_summary || {}, rm = c.reminder || {};
      var inp = function (id, label, v, type, ph) { return '<label>' + label + '<input id="' + id + '" type="' + (type || 'text') + '" value="' + esc(v == null ? '' : v) + '" placeholder="' + esc(ph || '') + '"></label>'; };
      var sel = function (id, label, opts, v) { return '<label>' + label + '<select id="' + id + '">' + opts.map(function (o) { return '<option value="' + o[0] + '"' + (o[0] === v ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select></label>'; };
      var warn = c.provider === 'none' ? '<div style="background:#fff7ed;border:1px solid #fdba74;color:#9a3412;border-radius:8px;padding:10px;margin-bottom:12px;font-size:13px"><b>Gönderim sağlayıcısı seçili değil.</b> Otomatik SMS için Verimor, WhatsApp için Twilio veya Webhook (Meta WhatsApp Cloud API / n8n / Make) bağlantısı girin; seçilmeden mesaj gönderilmez.</div>' : '';
      var dgh = dg ? '<div class="spx-card" style="border-color:' + (dg.all_ok ? '#86efac' : '#fdba74') + '"><b>Ayar kontrolü</b> ' + (dg.all_ok ? pill('hazır', '#16a34a') : pill('eksik var', '#f59e0b')) + dg.items.map(function (i) { return '<div style="display:flex;gap:8px;margin-top:6px;font-size:13px"><span>' + (i.ok ? '✅' : '❌') + '</span><span><b>' + esc(i.title) + '</b>' + (!i.ok && i.hint ? '<br><small style="color:#9a3412">' + esc(i.hint) + '</small>' : '') + '</span></div>'; }).join('') +
        (dg.recent_failed.length ? '<div style="margin-top:10px;font-size:13px"><b style="color:#dc2626">Son başarısız gönderimler</b>' + dg.recent_failed.map(function (f) { return '<div style="margin-top:4px;padding:6px 8px;background:#fef2f2;border-radius:8px"><small>' + esc((f.created_at || '').slice(0, 16).replace('T', ' ')) + ' · ' + esc(f.kind || '') + ' · ' + esc(f.to || '—') + '</small><br><b style="color:#b91c1c">' + esc(f.error || 'bilinmeyen hata') + '</b></div>'; }).join('') + '</div>' : '') + '</div>' : '';
      var h = dgh + warn +
        '<div class="spx-card"><b>1) Gönderim sağlayıcısı</b><div class="spx-g" style="margin-top:8px">' + sel('w_prov', 'Sağlayıcı', [['none', 'Seçili değil'], ['verimor', 'Verimor (SMS)'], ['twilio', 'Twilio (WhatsApp + SMS)'], ['webhook', 'Webhook (Meta Cloud API / n8n / Make)']], c.provider) + '</div>' +
        '<div id="w_vm" style="display:' + (c.provider === 'verimor' ? 'block' : 'none') + '"><div class="spx-g">' + inp('w_vu', 'Kullanıcı adı (908501234567 biçimi)', vm.username) + inp('w_vp', 'API şifresi (OİM > API şifresi)', vm.password, 'password') + inp('w_vs', 'Gönderici başlığı (onaylı başlık)', vm.source_addr) + '<div style="display:flex;align-items:flex-end"><button class="spx-b" id="w_vbal" type="button">Bakiyeyi sorgula</button></div></div><div id="w_vres" style="margin-top:6px;font-size:13px"></div><small style="color:#64748b;display:block;margin-top:6px">Verimor yalnızca SMS gönderir; kanalları (usta, müşteri, günlük özet) aşağıda “SMS” seçin. Sunucunun IP adresi Verimor OİM’de izinli olmalı. Şifre kaydedildikten sonra gizli tutulur.</small></div>' +
        '<div id="w_tw" style="display:' + (c.provider === 'twilio' ? 'block' : 'none') + '"><div class="spx-g">' + inp('w_sid', 'Account SID', tw.account_sid) + inp('w_tok', 'Auth Token', tw.auth_token, 'password') + inp('w_fwa', 'WhatsApp gönderen no (örn +14155238886)', tw.from_whatsapp) + inp('w_fsms', 'SMS gönderen no (isteğe bağlı)', tw.from_sms) + '</div></div>' +
        '<div id="w_wh" style="display:' + (c.provider === 'webhook' ? 'block' : 'none') + '"><div class="spx-g">' + inp('w_url', 'Webhook adresi', wh.url) + '<label style="grid-column:span 2">Başlıklar (satır satır, Ad: değer)<textarea id="w_hd" rows="2">' + esc(wh.headers || '') + '</textarea></label><label style="grid-column:span 2">Gövde şablonu ({channel} {to} {text} kullanılabilir)<textarea id="w_bd" rows="2">' + esc(wh.body_template || '') + '</textarea></label></div></div>' +
        '<small style="color:#64748b;display:block;margin-top:6px">WhatsApp kuralı: işletmenin kendi başlattığı mesajlar için Meta onaylı şablon gerekir; usta numarası işletme numarasına önce mesaj attıysa 24 saat içinde serbest metin gider. Sağlayıcıda şablon ayarlarını yapın.</small></div>' +
        '<div class="spx-card"><b>2) Ustaya atama mesajı</b><div style="margin-top:6px"><label class="spx-sw-l" style="display:flex;align-items:center;gap:8px">' + sw('w_ten', t.enabled == null ? cu.enabled : t.enabled) + ' Admin ustaya iş atayınca ustanın telefonuna otomatik gönder</label></div><div class="spx-g" style="margin-top:8px">' + sel('w_tch', 'Kanal', [['', 'Müşteri mesajıyla aynı'], ['whatsapp', 'WhatsApp'], ['sms', 'SMS']], t.channel || '') + inp('w_tbase', 'Panel adresi (mesajdaki link)', t.base_url) + '<label style="grid-column:span 2">Mesaj şablonu<textarea id="w_ttpl" rows="6">' + esc(t.template || '') + '</textarea></label></div><small style="color:#64748b">Değişkenler: {usta} {is_no} {musteri} {adres} {cihaz} {ariza} {zaman} {link}. Müşteri telefonu mesaja konmaz. Ustanın telefon numarası Ekip kaydında dolu olmalı.</small></div>' +
        '<div class="spx-card"><b>Yeni usta hesabı → giriş bilgileri</b><div style="margin-top:6px"><label style="display:flex;align-items:center;gap:8px">' + sw('w_wen', t.welcome_enabled == null ? cu.enabled : t.welcome_enabled) + ' Yeni usta eklenince (panelden manuel ya da başvuru onayı) ustaya link + kullanıcı adı + şifre gönder</label></div><label style="display:block;margin-top:8px">Mesaj şablonu<textarea id="w_wtpl" rows="5">' + esc(t.welcome_template || '') + '</textarea></label><small style="color:#64748b">Değişkenler: {ad} {link} {kullanici} {sifre}. Şifre gönderim kaydında (Son gönderimler) maskelenir. Ustanın telefonu kayıtlı olmalı.</small></div>' +
        '<div class="spx-card"><b>3) Müşteriye mesaj (usta atanınca)</b><div style="margin-top:6px"><label style="display:flex;align-items:center;gap:8px">' + sw('w_cen', cu.enabled) + ' Müşteriye otomatik mesaj gönder</label></div><div class="spx-g" style="margin-top:8px">' + sel('w_cch', 'Kanal', [['whatsapp', 'WhatsApp'], ['sms', 'SMS']], cu.channel || 'sms') + inp('w_cbase', 'Takip sitesi adresi', cu.base_url, 'text', 'https://bayi.servisplus.net.tr') + '<label style="grid-column:span 2">“Usta atandı” şablonu<textarea id="w_ctpl" rows="3">' + esc(((cu.templates || {}).assigned) || '') + '</textarea></label></div></div>' +
        '<div class="spx-card"><b>4) Günlük özet ve puanlama mesajı</b><div style="margin-top:6px"><label style="display:flex;align-items:center;gap:8px">' + sw('w_den', dsm.enabled) + ' Her sabah yöneticiye özet gönder (bugünkü iş, atanmamış, gecikmiş, bekleyen teklif, yeni mesaj)</label></div><div class="spx-g" style="margin-top:8px">' + sel('w_dch', 'Kanal', [['whatsapp', 'WhatsApp'], ['sms', 'SMS']], dsm.channel || 'whatsapp') + inp('w_dhr', 'Saat (0-23)', dsm.hour == null ? 8 : dsm.hour, 'number') + inp('w_dph', 'Alıcı telefonlar (virgülle ayırın)', (dsm.phones || []).join(', '), 'text', '05xx xxx xx xx') + '<div style="display:flex;align-items:flex-end"><button class="spx-b" id="w_dnow">Şimdi gönder (deneme)</button></div></div><div id="w_dres" style="margin-top:6px;font-size:13px"></div><label style="display:flex;align-items:center;gap:8px;margin-top:12px">' + sw('w_sen', (cu.events || {}).survey) + ' Servis bitip 2 saat sonra müşteriye puanlama mesajı gönder (müşteri mesajı açık olmalı)</label><label style="display:block;margin-top:8px">Puanlama şablonu<textarea id="w_stpl" rows="2">' + esc(((cu.templates || {}).survey) || '') + '</textarea></label><small style="color:#64748b">Otomatik gönderim için sağlayıcı seçili olmalı. Mesajdaki {link} takip sayfasına gider, müşteri oradan puan verir.</small></div>' +
        '<div class="spx-card"><b>5) Randevu hatırlatma</b><div style="margin-top:6px"><label style="display:flex;align-items:center;gap:8px">' + sw('w_ren', rm.enabled) + ' Randevu saatinden önce müşteriye ve ustaya otomatik hatırlatma gönder</label></div><div class="spx-g" style="margin-top:8px">' + inp('w_rmin', 'Kaç dakika önce', rm.minutes_before == null ? 60 : rm.minutes_before, 'number') + '<label style="display:flex;align-items:flex-end;gap:8px">' + sw('w_rcu', rm.customer !== false) + ' Müşteriye</label><label style="display:flex;align-items:flex-end;gap:8px">' + sw('w_rte', rm.technician !== false) + ' Ustaya</label><label style="grid-column:span 2">Müşteri şablonu ({ad} {zaman} {usta} {link} {is_no})<textarea id="w_rct" rows="2">' + esc(rm.customer_template || '') + '</textarea></label><label style="grid-column:span 2">Usta şablonu ({zaman} {musteri} {adres} {is_no} {link})<textarea id="w_rtt" rows="2">' + esc(rm.tech_template || '') + '</textarea></label></div><small style="color:#64748b">Randevu saati girilmiş açık işler için, her iş ve alıcıya yalnızca bir kez gider. Sağlayıcı (Verimor vb.) seçili olmalı; kontrol 5 dakikada bir yapılır.</small></div>' +
        '<div class="spx-card"><button class="spx-b p" id="w_save">Kaydet</button> <span style="margin-left:14px">Test:</span> <input id="w_tt" placeholder="05xx xxx xx xx" style="width:160px"> <select id="w_tc"><option value="whatsapp">WhatsApp</option><option value="sms">SMS</option></select> <button class="spx-b" id="w_test">Test mesajı gönder</button><div id="w_res" style="margin-top:8px;font-size:13px"></div></div>' +
        '<div class="spx-card"><b>Son gönderimler</b>' + tbl(['Zaman', 'Alıcı', 'Tür', 'Durum', 'Hata'], ob.map(function (o) { return tr_([o.created_at ? new Date(o.created_at).toLocaleString('tr-TR') : '', esc(o.to || ''), esc(o.kind || ''), pill(o.status === 'sent' ? 'gitti' : o.status === 'failed' ? 'hata' : o.status, o.status === 'sent' ? '#16a34a' : o.status === 'failed' ? '#dc2626' : ''), '<small>' + esc(o.error || '') + '</small>']); })) + '</div>';
      body().innerHTML = h;
      $('#w_prov').onchange = function () { $('#w_tw').style.display = this.value === 'twilio' ? 'block' : 'none'; $('#w_vm').style.display = this.value === 'verimor' ? 'block' : 'none'; $('#w_wh').style.display = this.value === 'webhook' ? 'block' : 'none'; };
      $('#w_save').onclick = function () {
        var pl = { provider: $('#w_prov').value, reminder: { enabled: $('#w_ren').checked, minutes_before: Math.max(5, Math.min(1440, parseInt($('#w_rmin').value, 10) || 60)), customer: $('#w_rcu').checked, technician: $('#w_rte').checked, customer_template: $('#w_rct').value, tech_template: $('#w_rtt').value }, technician: { welcome_enabled: $('#w_wen').checked, welcome_template: $('#w_wtpl').value, enabled: $('#w_ten').checked, channel: $('#w_tch').value, base_url: $('#w_tbase').value.trim(), template: $('#w_ttpl').value },
          customer: { enabled: $('#w_cen').checked, channel: $('#w_cch').value, base_url: $('#w_cbase').value.trim(), events: { survey: $('#w_sen').checked }, templates: { assigned: $('#w_ctpl').value, survey: $('#w_stpl').value } },
          daily_summary: { enabled: $('#w_den').checked, channel: $('#w_dch').value, hour: Math.max(0, Math.min(23, parseInt($('#w_dhr').value, 10) || 8)), phones: $('#w_dph').value.split(/[,;\n]/).map(function (x) { return x.trim(); }).filter(Boolean) } };
        if (pl.provider === 'verimor') pl.verimor = { username: $('#w_vu').value.trim(), password: $('#w_vp').value, source_addr: $('#w_vs').value.trim() };
        if (pl.provider === 'twilio') pl.twilio = { account_sid: $('#w_sid').value.trim(), auth_token: $('#w_tok').value, from_whatsapp: $('#w_fwa').value.trim(), from_sms: $('#w_fsms').value.trim() };
        if (pl.provider === 'webhook') pl.webhook = { url: $('#w_url').value.trim(), headers: $('#w_hd').value, body_template: $('#w_bd').value };
        call('PUT', '/governance/notify-settings', pl).then(function () { toast('Kaydedildi'); drawWa(); }).catch(fail);
      };
      $('#w_vbal').onclick = function () { $('#w_vres').textContent = 'Sorgulanıyor… (önce Kaydet’e basılmış olmalı)'; call('POST', '/governance/verimor-balance', {}).then(function (r) { $('#w_vres').innerHTML = '<b style="color:#16a34a">Bağlantı tamam ✔ Kalan kredi: ' + esc(r.balance) + '</b>'; }).catch(function (e) { $('#w_vres').innerHTML = '<b style="color:#dc2626">' + esc(e.message) + '</b>'; }); };
      if (c.provider === 'verimor') $('#w_tc').value = 'sms';
      $('#w_dnow').onclick = function () { $('#w_dres').textContent = 'Gönderiliyor…'; call('POST', '/governance/daily-summary-now', {}).then(function (r) { $('#w_dres').innerHTML = r.sent ? '<b style="color:#16a34a">Gönderildi ✔</b>' : '<b style="color:#dc2626">Gönderilemedi.</b> Telefon/sağlayıcıyı kontrol edin; sonuç aşağıdaki Son gönderimler listesinde.'; }).catch(function (e) { $('#w_dres').textContent = e.message; }); };
      $('#w_test').onclick = function () { $('#w_res').textContent = 'Gönderiliyor…'; call('POST', '/governance/notify-test', { channel: $('#w_tc').value, to: $('#w_tt').value }).then(function (r) { $('#w_res').innerHTML = r.status === 'sent' ? '<b style="color:#16a34a">Gönderildi ✔</b>' : '<b style="color:#dc2626">Gönderilemedi:</b> ' + esc(r.error || r.status); }).catch(function (e) { $('#w_res').textContent = e.message; }); };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }

  /* ===== Usta "QR Etiket": üstte ServisPlus logosu olan etiket ===== */
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('button, a'); if (!b || (b.textContent || '').trim() !== 'QR Etiket') return;
    var m = location.pathname.match(/^\/tech\/jobs\/([^\/?#]+)/); if (!m) return;
    e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
    var w = window.open('', '_blank'); if (!w) { toast('Açılır pencere engellendi — tarayıcıda bu siteye izin verin'); return; }
    w.document.write('<meta charset="utf-8"><body style="font:16px sans-serif;padding:24px">Etiket hazırlanıyor…</body>');
    var base = location.origin, tk = LS.get('token', '');
    Promise.all([pcall('GET', '/qr/jobs/' + m[1] + '?base=' + encodeURIComponent(base)),
      fetch(API + '/qr/jobs/' + m[1] + '/png?base=' + encodeURIComponent(base), { headers: { Authorization: 'Bearer ' + tk } }).then(function (r) { if (!r.ok) throw new Error('QR alınamadı'); return r.blob(); }).then(function (bl) { return new Promise(function (res) { var fr = new FileReader(); fr.onload = function () { res(fr.result); }; fr.readAsDataURL(bl); }); })
    ]).then(function (a) {
      var d = a[0], png = a[1], dev = [d.brand, d.model].filter(Boolean).join(' ') || d.type || '';
      var html = '<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>QR Etiket ' + esc(d.job_number || '') + '</title><style>@page{size:auto;margin:3mm}*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;color:#000;text-align:center}.l{width:62mm;margin:0 auto;padding:3mm 2mm;border:1px dashed #999}.lg{height:13mm;max-width:100%;object-fit:contain;display:block;margin:0 auto 2mm}.q{width:44mm;height:44mm;display:block;margin:0 auto;image-rendering:pixelated}.t{font-weight:700;font-size:12px;margin-top:2mm}.s{font-size:11px;margin-top:1mm}.n{font-size:10px;color:#333;margin-top:1mm}@media print{.l{border:0}.nb{display:none}}.nb{margin:10px;text-align:center}</style></head><body>' +
        '<div class="nb"><button onclick="window.print()" style="padding:10px 18px;font-size:15px">🖨 Yazdır</button></div>' +
        '<div class="l">' + (FIRM ? (FLOGO ? '<img class="lg" src="' + FLOGO + '" alt="">' : '<div class=t style="font-size:18px">' + esc(FIRM.name || '') + '</div>') : '<img class="lg" src="https://servisplus.net.tr/images/logo.png" alt="ServisPlus" onerror="this.outerHTML=\'<div class=t style=font-size:18px>ServisPlus</div>\'">') +
        '<img class="q" src="' + png + '" alt="QR"><div class="t">Cihaz Servis Etiketi</div><div class="s">' + esc(dev) + '</div><div class="n">Servis kaydı: ' + esc(d.job_number || '') + '</div><div class="n">Servis için QR kodu okutun' + (FIRM ? (FIRM.phone ? ' · ' + esc(FIRM.phone) : '') : ' · 0544 444 4 004') + '</div></div>' +
        '<script>window.addEventListener("load",function(){setTimeout(function(){window.print()},500)})<\/script></body></html>';
      w.document.open(); w.document.write(html); w.document.close();
    }).catch(function (er) { try { w.close(); } catch (x) { } toast(er.message || 'Etiket oluşturulamadı'); });
  }, true);


  /* ===== Elle WhatsApp (sağlayıcı gerekmez): ustaya iş bildirimi + yeni usta giriş bilgisi ===== */
  var WA_TECH_TPL = 'Merhaba {usta}, size yeni bir servis kaydı atandı.\nKayıt No: {is_no}\nMüşteri: {musteri}\nAdres: {adres}\nCihaz: {cihaz}\nArıza: {ariza}\nZaman: {zaman}\nKayıt detayı: {link}\nHayırlı işler dileriz.';
  var WA_WEL_TPL = 'Merhaba {ad}, ServisPlus usta paneline hoş geldiniz.\nGiriş adresi: {link}\nKullanıcı adı: {kullanici}\nŞifre: {sifre}\nGirişten sonra şifrenizi değiştirmenizi öneririz. Hayırlı işler dileriz.';
  function waNum(p) { var d = String(p || '').replace(/\D/g, ''); if (d.indexOf('00') === 0) d = d.slice(2); if (d.length === 10) d = '90' + d; else if (d.length === 11 && d.charAt(0) === '0') d = '9' + d; return d; }
  function waRender(t, v) { Object.keys(v).forEach(function (k) { t = t.split('{' + k + '}').join(v[k] == null ? '' : String(v[k])); }); return t.trim(); }
  function waOpen(phone, text) { var n = waNum(phone); window.open('https://wa.me/' + (n || '') + '?text=' + encodeURIComponent(text), '_blank'); }
  var WA_USTA_TPLS = [
    ['İş atandı', null],
    ['Hatırlatma', 'Merhaba {usta}, {is_no} numaralı servis kaydı için hatırlatma.\nMüşteri: {musteri}\nAdres: {adres}\nCihaz: {cihaz}\nZaman: {zaman}\nLütfen müşteriyle iletişime geçip durumu bildirin. Kayıt: {link}'],
    ['Durum sor', 'Merhaba {usta}, {is_no} numaralı ({musteri}) iş nasıl gidiyor? Güncel durumu panelden girebilir misiniz? Kayıt: {link}']
  ];
  function waJobSend(jid) {
    Promise.all([call('GET', '/jobs/' + jid), call('GET', '/technicians'), call('GET', '/governance/notify-settings').catch(function () { return {}; })]).then(function (a) {
      var j = a[0], t = (a[1] || []).filter(function (x) { return x.id === j.assigned_technician_id; })[0], cfg = (a[2] || {}).technician || {};
      if (!t) return toast('Önce bu kayda usta atayın');
      var base = (cfg.base_url || 'https://bayi.servisplus.net.tr').replace(/\/$/, '');
      var vals = { usta: (t.name || '').split(' ')[0], is_no: j.job_number || '', musteri: j.customer_name || '', adres: [j.customer_address, j.customer_district, j.customer_city].filter(Boolean).join(' '), cihaz: [j.device_brand_name, j.device_model, j.device_type].filter(Boolean).join(' '), ariza: (j.fault_description || '').slice(0, 300), zaman: j.scheduled_at ? String(j.scheduled_at).slice(0, 16).replace('T', ' ') : 'En kısa sürede', link: base + '/tech/jobs/' + jid };
      var old = document.getElementById('spx-wam'); if (old) old.remove();
      var m = document.createElement('div'); m.id = 'spx-wam'; m.className = 'notranslate';
      m.style.cssText = 'position:fixed;inset:0;z-index:100002;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:14px';
      var chip = function (i, on) { return '<button type="button" data-i="' + i + '" style="border:1px solid ' + (on ? '#2563eb' : '#e2e8f0') + ';background:' + (on ? '#2563eb' : '#fff') + ';color:' + (on ? '#fff' : '#0f172a') + ';border-radius:8px;padding:7px 12px;font-size:12px;font-weight:700;cursor:pointer">' + WA_USTA_TPLS[i][0] + '</button>'; };
      var bt = 'display:inline-flex;align-items:center;justify-content:center;gap:7px;border-radius:8px;padding:11px 14px;font-size:14px;font-weight:700;cursor:pointer;';
      m.innerHTML = '<div style="width:100%;max-width:400px;background:#fff;color:#0f172a;border-radius:14px;padding:20px;box-shadow:0 20px 60px rgba(0,0,0,.35);font-family:system-ui,sans-serif;position:relative"><button id="wam_x" style="position:absolute;right:14px;top:12px;border:0;background:none;font-size:18px;cursor:pointer;color:#475569">✕</button>' +
        '<div style="font-size:17px;font-weight:800;margin-bottom:6px">💬 Ustaya mesaj</div>' +
        '<div style="font-size:13px;color:#475569;line-height:1.45;margin-bottom:12px">Hazır mesaj ustanın (<b>' + esc(t.name || '') + '</b>) WhatsApp\'ında açılır; göndermek için WhatsApp\'ta "gönder"e basın. Metni göndermeden önce düzenleyebilirsiniz.</div>' +
        (waNum(t.phone) ? '' : '<div style="background:#fff7ed;color:#9a3412;border-radius:8px;padding:8px 10px;font-size:12px;margin-bottom:10px">Ustanın telefonu kayıtlı değil (Ekip → usta düzenle). WhatsApp açılınca numarayı kendiniz seçin.</div>') +
        '<div id="wam_c" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">' + WA_USTA_TPLS.map(function (x, i) { return chip(i, i === 0); }).join('') + '</div>' +
        '<textarea id="wam_t" rows="9" style="width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:10px;font-size:14px;line-height:1.45;color:#0f172a;background:#fff;resize:vertical"></textarea>' +
        '<div style="display:flex;gap:8px;margin-top:12px"><button id="wam_go" style="' + bt + 'flex:1;background:#059669;color:#fff;border:0">💬 WhatsApp\'ta aç</button><button id="wam_cp" style="' + bt + 'background:#fff;color:#0f172a;border:1px solid #cbd5e1">⧉ Kopyala</button><button id="wam_ln" style="' + bt + 'background:#fff;color:#0f172a;border:1px solid #cbd5e1">🔗 Link</button></div></div>';
      document.body.appendChild(m);
      var ta = m.querySelector('#wam_t'), cur = 0;
      var fill = function (i) { cur = i; ta.value = waRender(WA_USTA_TPLS[i][1] || cfg.template || WA_TECH_TPL, vals); m.querySelector('#wam_c').innerHTML = WA_USTA_TPLS.map(function (x, k) { return chip(k, k === i); }).join(''); };
      fill(0);
      var url = function () { return 'https://wa.me/' + (waNum(t.phone) || '') + '?text=' + encodeURIComponent(ta.value); };
      var copy = function (txt, ok) { var d = function () { var x = document.createElement('textarea'); x.value = txt; document.body.appendChild(x); x.select(); try { document.execCommand('copy'); } catch (e) { } x.remove(); toast(ok); }; if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(function () { toast(ok); }, d); else d(); };
      m.querySelector('#wam_c').onclick = function (e) { var b = e.target.closest('button[data-i]'); if (b) fill(+b.getAttribute('data-i')); };
      m.querySelector('#wam_x').onclick = function () { m.remove(); };
      m.addEventListener('mousedown', function (e) { if (e.target === m) m.remove(); });
      m.querySelector('#wam_go').onclick = function () { window.open(url(), '_blank'); };
      m.querySelector('#wam_cp').onclick = function () { copy(ta.value, 'Mesaj kopyalandı'); };
      m.querySelector('#wam_ln').onclick = function () { copy(url(), 'WhatsApp linki kopyalandı'); };
    }).catch(function (er) { toast(er.message || 'Mesaj hazırlanamadı'); });
  }
  function jobWaBtn() {
    var m = location.pathname.match(/^\/admin\/jobs\/([^\/?#]+)\/?$/), ex = document.getElementById('spx-wa-usta');
    if (!m) { if (ex) ex.remove(); return; }
    if (ex) return;
    var pdf = Array.prototype.filter.call(document.querySelectorAll('main button, main a'), function (b) { return /^\s*PDF İndir\s*$/.test(b.textContent || ''); })[0]; if (!pdf || !pdf.parentNode) return;
    var b = pdf.cloneNode(true); b.id = 'spx-wa-usta'; b.removeAttribute('href'); b.removeAttribute('disabled'); b.setAttribute('type', 'button'); b.setAttribute('data-j', m[1]);
    var w = document.createTreeWalker(b, NodeFilter.SHOW_TEXT), n, done = false; while ((n = w.nextNode())) { if (!done && n.nodeValue.trim()) { n.nodeValue = 'Ustaya WhatsApp'; done = true; } else if (done) n.nodeValue = ''; }
    if (!done) b.textContent = 'Ustaya WhatsApp';
    b.style.setProperty('color', '#15803d', 'important');
    b.onclick = function (e) { e.preventDefault(); e.stopPropagation(); waJobSend(m[1]); };
    pdf.parentNode.insertBefore(b, pdf);
  }
  setInterval(jobWaBtn, 800);
  function jobAssignCard(jid, tname) {
    var old = document.getElementById('spx-wel'); if (old) old.remove();
    var c = document.createElement('div'); c.id = 'spx-wel'; c.className = 'notranslate';
    c.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:100001;background:#fff;border:1px solid #cbd5e1;border-left:5px solid #16a34a;border-radius:12px;padding:14px;box-shadow:0 8px 30px rgba(0,0,0,.2);max-width:340px;color:#0f172a;font:14px system-ui,sans-serif';
    c.innerHTML = '<div style="display:flex;justify-content:space-between;gap:10px"><b>✅ Usta atandı</b><button id="spx-wel-x" style="border:0;background:none;font-size:16px;cursor:pointer">✕</button></div><div style="margin:6px 0 10px;color:#475569">' + esc(tname || 'Usta') + ' için iş bilgisini WhatsApp ile gönderin.</div><button id="spx-wel-go" style="width:100%;background:#16a34a;color:#fff;border:0;border-radius:10px;padding:11px;font-size:15px;font-weight:700;cursor:pointer">📲 Ustaya WhatsApp gönder</button>';
    document.body.appendChild(c);
    c.querySelector('#spx-wel-x').onclick = function () { c.remove(); };
    c.querySelector('#spx-wel-go').onclick = function () { waJobSend(jid); c.remove(); };
  }
  function welCard(name, phone, email, pass, tid) {
    var old = document.getElementById('spx-wel'); if (old) old.remove();
    var c = document.createElement('div'); c.id = 'spx-wel'; c.className = 'notranslate';
    c.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:100001;background:#fff;border:1px solid #cbd5e1;border-left:5px solid #16a34a;border-radius:12px;padding:14px;box-shadow:0 8px 30px rgba(0,0,0,.2);max-width:340px;color:#0f172a;font:14px system-ui,sans-serif';
    c.innerHTML = '<div style="display:flex;justify-content:space-between;gap:10px"><b>✅ Usta hesabı oluştu</b><button id="spx-wel-x" style="border:0;background:none;font-size:16px;cursor:pointer">✕</button></div><div style="margin:6px 0 10px;color:#475569">' + esc(name || '') + ' için giriş bilgilerini WhatsApp ile gönderin.</div>' + (waNum(phone) ? '' : '<div style="color:#b45309;margin-bottom:8px">Telefon yok: WhatsApp açılınca numarayı kendiniz seçin.</div>') + '<button id="spx-wel-go" style="width:100%;background:#16a34a;color:#fff;border:0;border-radius:9px;padding:11px;font-size:15px;font-weight:700;cursor:pointer">📲 WhatsApp ile gönder</button>' + (tid ? '<button id="spx-wel-dt" style="width:100%;margin-top:8px;background:#fff;color:#0a1f44;border:1px solid #cbd5e1;border-radius:9px;padding:10px;font-size:14px;font-weight:700;cursor:pointer">📋 Usta detaylarını doldur (il, ilçe, grup, not)</button>' : '');
    document.body.appendChild(c);
    var dtb = c.querySelector('#spx-wel-dt'); if (dtb) dtb.onclick = function () { techProfModal(tid); };
    c.querySelector('#spx-wel-x').onclick = function () { c.remove(); };
    c.querySelector('#spx-wel-go').onclick = function () { waOpen(phone, waRender(WA_WEL_TPL, { ad: String(name || '').split(' ')[0], link: 'https://bayi.servisplus.net.tr/login', kullanici: email, sifre: pass })); };
  }
  (function () {
    var sd = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function (b) {
      try {
        var x = this, mt = x._spx && x._spx[0], u = x._spx ? x._spx[1].split('?')[0] : '';
        if ((mt === 'POST' && /\/jobs\/quick$/.test(u)) || (mt === 'POST' && /\/jobs\/[^\/]+\/reassign$/.test(u))) {
          var rq = {}; try { rq = JSON.parse(b || '{}'); } catch (e) { }
          if (rq.assigned_technician_id || rq.technician_id || /reassign$/.test(u)) x.addEventListener('load', function () {
            if (x.status < 200 || x.status > 299) return;
            var rj = {}; try { rj = JSON.parse(x.responseText || '{}'); } catch (e) { }
            if (rj.id && rj.assigned_technician_id) jobAssignCard(rj.id, rj.assigned_technician_name);
          });
        }
        if (mt === 'POST' && (/\/technicians$/.test(u) || /\/dealers\/[^\/]+\/create-technician$/.test(u))) {
          var req = {}; try { req = JSON.parse(b || '{}'); } catch (e) { }
          x.addEventListener('load', function () {
            if (x.status < 200 || x.status > 299) return;
            var r = {}; try { r = JSON.parse(x.responseText || '{}'); } catch (e) { }
            welCard(r.name || req.name, r.phone || req.phone, r.email || req.email, r.password || req.password, r.id || r.technician_id);
          });
        }
      } catch (e) { }
      return sd.call(this, b);
    };
  })();

  /* ---------- admin: listelerde satır başına kare kutu + toplu silme ---------- */
  var BK = [ // [satırı/butonu bulan seçici, testid öneki, silme adresi, ad]
    ['[data-testid^="job-row-"]', 'job-row-', '/jobs/', 'servis kaydı', 1],
    ['[data-testid^="delete-customer-"]', 'delete-customer-', '/customers/', 'müşteri'],
    ['[data-testid^="delete-tech-"]', 'delete-tech-', '/technicians/', 'teknisyen'],
    ['[data-testid^="delete-part-"]', 'delete-part-', '/parts/', 'yedek parça'],
    ['[data-testid^="delete-brand-"]', 'delete-brand-', '/brands/', 'marka'],
    ['[data-testid^="delete-apt-"]', 'delete-apt-', '/appointments/', 'randevu'],
    ['[data-testid^="delete-tx-"]', 'delete-tx-', '/cash/transactions/', 'muhasebe hareketi'],
    ['[data-testid^="quote-card-"]', 'quote-card-', '/quotes/', 'fiyat teklifi', 1],
    ['[data-testid^="dealer-row-"]', 'dealer-row-', '/dealers/', 'bayilik başvurusu', 1],
    ['[data-testid^="delete-admin-"]', 'delete-admin-', '/admin-users/', 'yönetici']
  ];
  var BSEL = {}, BPATH = '';
  function bkRow(el, pre) { // silme butonundan satırın kendisini bul: kardeşleri de aynı türde buton taşıyan en yakın ata
    var n = el.parentElement, sel = '[data-testid^="' + pre + '"]';
    for (var i = 0; i < 8 && n && n.parentElement; i++, n = n.parentElement) {
      var sib = [].filter.call(n.parentElement.children, function (c) { return c.querySelector(sel); });
      if (sib.length >= 2 || (n.tagName === 'TR')) return n;
    }
    return el.closest('tr') || el.parentElement.parentElement;
  }
  function bkBar() {
    var b = document.getElementById('spx-bk');
    if (!b) {
      b = document.createElement('div'); b.id = 'spx-bk'; b.className = 'notranslate';
      b.style.cssText = 'background:#0a1f44;color:#fff;border-radius:6px;padding:8px 12px;margin:8px 0 12px;display:none;gap:10px;justify-content:space-between;align-items:center;font-size:14px;flex-wrap:wrap';
      b.innerHTML = '<label style="display:flex;gap:6px;align-items:center;cursor:pointer"><input type="checkbox" id="spx-bk-all"> Sayfadakilerin tümü</label><b id="spx-bk-n">0 seçili</b><button id="spx-bk-del" style="border:0;background:#dc2626;color:#fff;border-radius:9px;padding:8px 14px;font-weight:700;cursor:pointer">Seçilenleri sil</button><button id="spx-bk-clr" style="border:1px solid #64748b;background:none;color:#fff;border-radius:9px;padding:7px 12px;cursor:pointer">Temizle</button>';
      document.body.appendChild(b);
      b.querySelector('#spx-bk-all').onchange = function () { var on = this.checked; [].forEach.call(document.querySelectorAll('.spx-bkc'), function (c) { c.checked = on; if (on) BSEL[c.getAttribute('data-k')] = { u: c.getAttribute('data-u'), n: c.getAttribute('data-n') }; else delete BSEL[c.getAttribute('data-k')]; }); bkCount(); };
      b.querySelector('#spx-bk-clr').onclick = function () { BSEL = {}; [].forEach.call(document.querySelectorAll('.spx-bkc'), function (c) { c.checked = false; }); bkCount(); };
      b.querySelector('#spx-bk-del').onclick = bkDelete;
    }
    return b;
  }
  function bkCount() { var n = Object.keys(BSEL).length, b = bkBar(); b.style.display = n ? 'flex' : 'none'; b.querySelector('#spx-bk-n').textContent = n + ' seçili'; b.querySelector('#spx-bk-del').disabled = !n; b.querySelector('#spx-bk-del').style.opacity = n ? 1 : .5; var all = document.querySelectorAll('.spx-bkc'), chk = [].filter.call(all, function (c) { return c.checked; }).length; b.querySelector('#spx-bk-all').checked = all.length > 0 && chk === all.length; }
  function bkDelete() {
    var keys = Object.keys(BSEL); if (!keys.length) return;
    var kinds = {}; keys.forEach(function (k) { kinds[BSEL[k].n] = (kinds[BSEL[k].n] || 0) + 1; });
    var desc = Object.keys(kinds).map(function (k) { return kinds[k] + ' ' + k; }).join(', ');
    if (!window.confirm(desc + ' kalıcı olarak silinecek. Bu işlem geri alınamaz. Devam edilsin mi?')) return;
    var btn = document.getElementById('spx-bk-del'); btn.disabled = true; btn.textContent = 'Siliniyor…';
    var ok = 0, errs = [], i = 0;
    (function next() {
      if (i >= keys.length) { toast(ok + ' kayıt silindi' + (errs.length ? ', ' + errs.length + ' silinemedi: ' + errs[0] : '')); BSEL = {}; btn.textContent = 'Seçilenleri sil'; if (ok) setTimeout(function () { location.reload(); }, errs.length ? 2500 : 700); else bkCount(); return; }
      var k = keys[i++], x = BSEL[k];
      call('DELETE', x.u + encodeURIComponent(k.split('|')[1])).then(function () { ok++; }).catch(function (e) { errs.push(e.message || 'hata'); }).then(next);
    })();
  }
  function bulkSel() {
    var on = !document.body.classList.contains('spx-tech') && /^\/admin(\/|$)/.test(location.pathname) && !/\/login/.test(location.pathname);
    if (BPATH !== location.pathname) { BPATH = location.pathname; BSEL = {}; }
    var bar = document.getElementById('spx-bk');
    if (!on) { if (bar) bar.style.display = 'none'; return; }
    if (!Object.keys(BSEL).length && bar) bar.style.display = 'none';
    var any = 0;
    BK.forEach(function (d) {
      [].forEach.call(document.querySelectorAll(d[0]), function (el) {
        var id = el.getAttribute('data-testid').slice(d[1].length); if (!id) return;
        var row = d[4] ? el : bkRow(el, d[1]); if (!row) return;
        any++;
        if (row.getAttribute('data-bk')) return; row.setAttribute('data-bk', '1');
        var key = d[1] + '|' + id, c = document.createElement('input'); c.type = 'checkbox'; c.className = 'spx-bkc'; c.setAttribute('data-k', key); c.setAttribute('data-u', d[2]); c.setAttribute('data-n', d[3]); c.title = 'Toplu işlem için seç'; c.checked = !!BSEL[key];
        var tr = row.tagName === 'TR';
        c.style.cssText = 'width:17px;height:17px;cursor:pointer;accent-color:#1d4ed8;' + (tr ? 'margin-right:8px;vertical-align:middle' : 'position:absolute;top:8px;left:8px;z-index:5');
        c.onclick = function (e) { e.stopPropagation(); }; c.onchange = function () { if (this.checked) BSEL[key] = { u: d[2], n: d[3] }; else delete BSEL[key]; bkCount(); };
        if (tr) { var td = row.querySelector('td'); if (td) td.insertBefore(c, td.firstChild); }
        else { var cs = getComputedStyle(row); if (cs.position === 'static') row.style.position = 'relative'; if ((parseFloat(cs.paddingLeft) || 0) < 34) row.style.paddingLeft = '34px'; c.style.top = '12px'; c.style.left = '10px'; row.appendChild(c); }   /* G177: kutu başlığın üstüne binmesin */
      });
    });
    if (any) bkCount(); else bkBar().style.display = 'none';
  }
  setInterval(bulkSel, 800);

  var t0 = null; new MutationObserver(function () { clearTimeout(t0); t0 = setTimeout(tick, 100); }).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('popstate', function () { setTimeout(markActive, 30); });
  tick();
  window.spxOpen = open;
  /* Bildirimden gelen derin baglanti: /admin?ek=sohbet gibi adresler ilgili bolumu acar */
  (function () {
    var q = ''; try { q = new URLSearchParams(location.search).get('ek') || ''; } catch (e) { }
    if (!q || !/^\/admin(\/|$)/.test(location.pathname)) return;
    var n = 0, tt = setInterval(function () {
      if (++n > 60) { clearInterval(tt); return; }
      var tk = ''; try { tk = localStorage.getItem('token') || ''; } catch (e) { }
      if (!tk || !document.body || document.body.classList.contains('spx-tech')) return;
      clearInterval(tt);
      try { open(q); history.replaceState({}, '', location.pathname); } catch (e) { }
    }, 500);
  })();

  /* ===== Admin mobil alt cubuk + "Daha Fazlasi" sayfasi + Bildirimler ===== */
  var MI = {
    home: '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h5v-6h4v6h5V10"/>', jobs: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
    live: '<circle cx="12" cy="12" r="2"/><path d="M16.2 7.8a6 6 0 0 1 0 8.4M7.8 16.2a6 6 0 0 1 0-8.4M19 5a10 10 0 0 1 0 14M5 19A10 10 0 0 1 5 5"/>',
    bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>', more: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>', tech: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/><path d="M18.5 3.5l1 1 2-2"/>',
    money: '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/><path d="M6 12h.01M18 12h.01"/>', cash: '<path d="M12 2v20M17 6.5C16 5 14.2 4.5 12 4.5c-2.8 0-4.5 1.3-4.5 3.3 0 4.7 9.5 2.3 9.5 7 0 2-1.9 3.2-5 3.2-2.3 0-4.2-.7-5.2-2.2"/>',
    cal: '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M8 2v4M16 2v4M3 10h18"/>', doc: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    msg: '<path d="M21 12a8 8 0 0 1-11.6 7.1L3 21l1.9-6.3A8 8 0 1 1 21 12z"/>', chart: '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>', shop: '<path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18M16 10a4 4 0 0 1-8 0"/>',
    star: '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.3-6.2 3.3L8 14.2l-5-4.9 6.9-1z"/>', shield: '<path d="M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5z"/><path d="M9 12l2 2 4-4"/>',
    box: '<path d="M21 8l-9-5-9 5v8l9 5 9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/>', gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    megaphone: '<path d="M3 11v2a1 1 0 0 0 1 1h3l8 4V6L7 10H4a1 1 0 0 0-1 1z"/><path d="M18.5 8.5a5 5 0 0 1 0 7"/>', brush: '<path d="M9.5 14.5L18 6a2 2 0 0 1 3 3l-8.5 8.5"/><path d="M9.5 14.5c-2.5 0-4 1.5-4 4 0 1-.8 1.5-1.5 2 3 .8 7-.5 7-3.5a2.5 2.5 0 0 0-1.5-2.5z"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>', menu: '<path d="M4 6h16M4 12h16M4 18h16"/>', warn: '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>'
  };
  function mi(k, sz) { return '<svg width="' + (sz || 22) + '" height="' + (sz || 22) + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">' + MI[k] + '</svg>'; }
  var MB_ITEMS = [['/admin', 'Ana Sayfa', 'home'], ['/admin/jobs', 'Servis', 'jobs'], ['ek:canli', 'Canlı', 'live'], ['ek:bildirim', 'Bildirimler', 'bell'], ['ek:daha', 'Daha Fazlası', 'more']];
  function mbGo(k) {
    if (k.indexOf('ek:') === 0) { open(k.slice(3)); return; }
    if (ov) ov.classList.remove('on');
    if (location.pathname.replace(/\/$/, '') !== k) goto(k); else window.scrollTo(0, 0);
    setTimeout(markActive, 50); setTimeout(mbar, 120);
  }
  (function () {
    var st = document.createElement('style');
    st.textContent = '#spx-mb{display:none}@media(max-width:1023px){body.spx-mbar{padding-bottom:70px}body.spx-mbar #spx-mb{display:flex}body.spx-mbar #spx-bk{bottom:76px!important}body.spx-mbar #spx-body{padding-bottom:84px}body.spx-mbar #spx-toast{bottom:84px}}' +
      '#spx-mb{position:fixed;left:0;right:0;bottom:0;z-index:45;background:#fff;border-top:1px solid #e2e8f0;box-shadow:0 -4px 20px rgba(15,23,42,.08);padding:6px 4px calc(6px + env(safe-area-inset-bottom));justify-content:space-around}' +
      '#spx-mb button{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;border:0;background:none;color:#64748b;font-size:10.5px;font-weight:600;padding:4px 0;position:relative;cursor:pointer;-webkit-tap-highlight-color:transparent}#spx-mb button.on{color:#1d4ed8}' +
      '#spx-mb button.on .mbi{background:#dbeafe}.mbi{width:46px;height:28px;border-radius:99px;display:flex;align-items:center;justify-content:center;transition:background .15s}' +
      '#spx-mb .mbb{position:absolute;top:0;left:calc(50% + 6px);background:#ef4444;color:#fff;font-size:10px;font-weight:700;border-radius:99px;min-width:16px;height:16px;padding:0 4px;display:flex;align-items:center;justify-content:center;line-height:1}' +
      '.spx-dg{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.spx-dg a{display:flex;flex-direction:column;align-items:center;gap:8px;background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:14px 6px 12px;text-decoration:none;color:#0f172a;font-size:12.5px;font-weight:600;text-align:center;line-height:1.25;position:relative;box-shadow:0 1px 2px rgba(15,23,42,.04)}.spx-dg a:active{transform:scale(.97)}' +
      '.spx-dg .ic{width:46px;height:46px;border-radius:14px;display:flex;align-items:center;justify-content:center;color:#fff}.spx-dg .bd{position:absolute;top:6px;right:8px;background:#ef4444;color:#fff;font-size:10px;font-weight:700;border-radius:99px;min-width:16px;height:16px;padding:0 4px;display:flex;align-items:center;justify-content:center}' +
      '.spx-dh{font-size:12px;font-weight:700;letter-spacing:.06em;color:#64748b;text-transform:uppercase;margin:4px 2px 10px}' +
      '.spx-bl a{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:12px;margin-bottom:8px;text-decoration:none;color:#0f172a}.spx-bl .ic{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;flex:none}.spx-bl .t{flex:1;font-weight:600;font-size:14px}.spx-bl .t small{display:block;font-weight:400;color:#64748b;font-size:12px}.spx-bl .n{font-weight:800;font-size:16px;min-width:28px;text-align:center;border-radius:99px;padding:2px 9px}' +
      '@media(prefers-color-scheme:dark){html.dark #spx-mb{background:#0f172a;border-color:#1e293b}html.dark .spx-dg a,html.dark .spx-bl a{background:#1e293b;border-color:#334155;color:#f1f5f9}}';
    document.head.appendChild(st);
  })();
  var MBAR_SIG = '';
  function mbar() {
    var u = me(), path = location.pathname, isAdm = /^\/admin(\/|$)/.test(path) && !document.body.classList.contains('spx-tech') && (!u.role || u.role === 'admin') && !!document.querySelector('[data-spx-own]');
    var b = document.getElementById('spx-mb');
    if (!isAdm) { if (b) b.remove(); document.body.classList.remove('spx-mbar'); MBAR_SIG = ''; return; }
    var items = MB_ITEMS.filter(function (it) { return it[0] === 'ek:bildirim' || it[0] === 'ek:daha' || canMenu(it[0]); });
    var ovOn = ov && ov.classList.contains('on'), cur = location.pathname.replace(/\/$/, '') || '/admin';
    var bd = { '/admin/jobs': ADMB ? (ADMB['/admin/jobs'] || 0) + (ADMB.jobs_overdue || 0) + (ADMB.call_overdue || 0) : 0, 'ek:bildirim': ADMB ? ADMB.total || 0 : 0, 'ek:canli': ADMB ? ADMB.live_visitors || 0 : 0 };
    var sig = items.map(function (it) { var on = it[0].indexOf('ek:') === 0 ? (ovOn && TAB === it[0].slice(3)) : (!ovOn && (it[0] === '/admin' ? cur === '/admin' : (cur === it[0] || cur.indexOf(it[0] + '/') === 0))); return it[0] + (on ? '*' : '') + (bd[it[0]] || ''); }).join('|');
    if (!b) { b = document.createElement('div'); b.id = 'spx-mb'; b.className = 'notranslate'; b.onclick = function (e) { var x = e.target.closest('button[data-k]'); if (x) mbGo(x.getAttribute('data-k')); }; document.body.appendChild(b); MBAR_SIG = ''; }
    document.body.classList.add('spx-mbar');
    if (sig === MBAR_SIG) return; MBAR_SIG = sig;
    b.innerHTML = items.map(function (it) {
      var on = sig.indexOf(it[0] + '*') >= 0, n = bd[it[0]] || 0;
      return '<button type="button" data-k="' + it[0] + '"' + (on ? ' class="on"' : '') + '><span class="mbi">' + mi(it[2]) + '</span>' + (n > 0 ? '<span class="mbb"' + (it[0] === 'ek:canli' ? ' style="background:#16a34a"' : '') + '>' + (n > 99 ? '99+' : n) + '</span>' : '') + '<span>' + it[1] + '</span></button>';
    }).join('');
  }
  setInterval(mbar, 600);
  var DAHA = [
    ['/admin/customers', 'Müşteriler', 'users', '#2563eb'], ['/admin/technicians', 'Teknisyenler', 'tech', '#0ea5e9'], ['/admin/accounting', 'Muhasebe', 'money', '#16a34a'],
    ['ek:tahsilat', 'Usta Tahsilat', 'cash', '#f59e0b'], ['/admin/appointments', 'Randevular', 'cal', '#8b5cf6'], ['/admin/quotes', 'Fiyat Teklifleri', 'doc', '#ec4899'],
    ['ek:atolye', 'Atölye', 'gear', '#64748b'], ['ek:harita', 'İş Haritası', 'live', '#0891b2'], ['ek:vade', 'Usta Vadesi', 'cal', '#c2410c'], ['ek:memnun', 'Memnuniyet', 'star', '#ca8a04'], ['ek:ustagecmis', 'Usta İş Geçmişi', 'chart', '#0d9488'], ['/admin/messages', 'Mesajlar', 'msg', '#f97316'],
    ['ek:rapor', 'Rapor Merkezi', 'chart', '#6366f1'], ['/admin/reports', 'Raporlar', 'chart', '#6366f1'], ['/admin/shop', 'Mağaza', 'shop', '#d946ef'], ['/admin/reviews', 'Yorumlar', 'star', '#eab308'],
    ['/admin/warranty', 'Garanti', 'shield', '#14b8a6'], ['/admin/parts', 'Yedek Parça', 'box', '#78716c'], ['/admin/dealers', 'Bayilik Başvuruları', 'users', '#0284c7'],
    ['/admin/marketing', 'Pazarlama', 'megaphone', '#e11d48'], ['/admin/site-studio', 'Site Stüdyosu', 'brush', '#7c3aed'], ['ek:seo', 'SEO', 'search', '#059669'],
    ['/admin/settings', 'Ayarlar', 'gear', '#475569'], ['ek:kurulum', 'Kurulum Durumu', 'shield', '#16a34a'], ['/admin/announcements', 'Duyurular', 'megaphone', '#ea580c'], ['/admin/governance', 'Yedek & Güvenlik', 'shield', '#b91c1c']
  ];
  var DAHA_BD = { '/admin/quotes': '/admin/quotes', '/admin/messages': 'messages', '/admin/technicians': '/admin/technicians' };
  function drawDaha() {
    var items = DAHA.filter(function (it) { return canMenu(it[0]); });
    body().innerHTML = '<div class="spx-dh">En çok kullanılanlar</div><div class="spx-dg">' + items.map(function (it) {
      var n = ADMB && DAHA_BD[it[0]] ? (ADMB[DAHA_BD[it[0]]] || 0) : 0;
      return '<a href="#" data-k="' + it[0] + '"><span class="ic" style="background:' + it[3] + '">' + mi(it[2], 24) + '</span>' + (n > 0 ? '<span class="bd">' + (n > 99 ? '99+' : n) + '</span>' : '') + esc(it[1]) + '</a>';
    }).join('') + '</div><div style="margin-top:16px"><button class="spx-b" id="spx-allmenu" style="width:100%;padding:12px">☰ Tüm menüyü aç</button></div>' + fontCard();
    body().onclick = function (e) {
      var a = e.target.closest('a[data-k]'); if (a) { e.preventDefault(); mbGo(a.getAttribute('data-k')); return; }
      if (e.target.closest('#spx-allmenu')) { var o = document.querySelector('[data-testid=open-sidebar]'); if (o) o.click(); }
    };
  }
  function drawBildirim() {
    var B = body(); B.innerHTML = '<div class="spx-dh">Yükleniyor…</div>';
    Promise.all([pcall('GET', '/admin/badges'), pcall('GET', '/reports/satisfaction?days=7').catch(function () { return { low: [] }; }), pcall('GET', '/tech-due').catch(function () { return { overdue_n: 0 }; })]).then(function (z) {
      var r = z[0]; r._low = (z[1].low || []).length; r._due = z[2].overdue_n || 0; ADMB = r;
      var rows = [['/admin/jobs', 'Yeni servis kaydı', 'Henüz işleme alınmadı', r['/admin/jobs'], 'jobs', '#2563eb'], ['/admin/jobs', 'Gecikmiş iş', 'Randevu saati geçti, kapanmadı', r.jobs_overdue, 'warn', '#dc2626'],
        ['/admin/jobs', 'Müşteri aranmadı', 'Usta, atanan işte süresinde aramadı', r.call_overdue, 'warn', '#b91c1c'], ['/admin/quotes', 'Bekleyen fiyat teklifi', 'Yanıt bekliyor', r['/admin/quotes'], 'doc', '#ec4899'], ['/admin/messages', 'Yeni mesaj', 'İletişim formundan geldi', r.messages, 'msg', '#f97316'],
        ['/admin/dealers', 'Bayilik başvurusu', 'İncelenmedi', r.dealers, 'users', '#0284c7'], ['/admin/warranty', 'Açık garanti talebi', 'Açık / inceleniyor', r.warranty, 'shield', '#14b8a6'],
        ['/admin/reviews', 'Onay bekleyen yorum', 'Yayın onayı bekliyor', r.reviews, 'star', '#eab308'], ['/admin/technicians', 'Borçlu usta', 'Bakiyesi açık olan ustalar', r['/admin/technicians'], 'tech', '#0ea5e9'],
        ['/admin/governance', 'Yedek uyarısı', 'Otomatik yedek gecikmiş', r.backup_stale, 'warn', '#b91c1c'], ['ek:memnun', 'Düşük puanlı iş (7 gün)', 'Müşteriyi arayın', r._low, 'star', '#ca8a04'], ['ek:vade', 'Vadesi geçen usta borcu', 'Hatırlatma gönderin', r._due, 'cart', '#c2410c']].filter(function (x) { return x[3] > 0 && canMenu(x[0]); });
      var h = '<div class="spx-dh">Dikkat gerektirenler</div>';
      if (!rows.length) h += '<div class="spx-card" style="text-align:center;padding:28px 14px"><div style="font-size:34px">✅</div><b>Bekleyen bir şey yok</b><div style="color:#64748b;font-size:13px;margin-top:4px">Yeni kayıt, mesaj veya teklif geldiğinde burada görünür.</div></div>';
      else h += '<div class="spx-bl">' + rows.map(function (x) { return '<a href="#" data-k="' + x[0] + '"><span class="ic" style="background:' + x[5] + '1a;color:' + x[5] + '">' + mi(x[4], 22) + '</span><span class="t">' + esc(x[1]) + '<small>' + esc(x[2]) + '</small></span><span class="n" style="background:' + x[5] + '1a;color:' + x[5] + '">' + x[3] + '</span></a>'; }).join('') + '</div>';
      if (canMenu('ek:wa')) h += '<div class="spx-dh" style="margin-top:14px">Ayar</div><div class="spx-bl"><a href="#" data-k="ek:wa"><span class="ic" style="background:#16a34a1a;color:#16a34a">' + mi('bell', 22) + '</span><span class="t">WhatsApp & telefon bildirimleri<small>Bildirim kanallarını aç / kapat</small></span></a></div>';
      B.innerHTML = h;
    }).catch(function () { B.innerHTML = '<div class="spx-card">Bildirimler yüklenemedi. Bağlantınızı kontrol edip tekrar deneyin.</div>'; });
    B.onclick = function (e) { var a = e.target.closest('a[data-k]'); if (a) { e.preventDefault(); mbGo(a.getAttribute('data-k')); } };
  }



  /* ===== GUNCELLEME 172: Onay Bekleyenler (usta/musteri fotograflari, is fotograflari, yorumlar) ===== */
  function drawOnay() {
    call('GET', '/foto/bekleyen').then(function (d) {
      window.__onayN = d.total || 0;
      var B = 'border:1px solid #cbd5e1;background:#fff;color:#0f172a;border-radius:6px;padding:6px 12px;font:inherit;font-size:13px;cursor:pointer;margin-right:6px', O = 'border:1px solid #0a1f44;background:#0a1f44;color:#fff;border-radius:6px;padding:6px 12px;font:inherit;font-size:13px;cursor:pointer;margin-right:6px';
      var tk = encodeURIComponent(LS.get('token', '')), h = '';
      h += '<div class="spx-card" style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;justify-content:space-between"><div><b>Onay bekleyen: ' + (d.total || 0) + '</b><small style="display:block;color:#64748b">Onaylamadığınız içerik müşteriye/ustaya görünmez; iş, puan ve süreç aynen devam eder. Onayladığınız anda görünür olur.</small></div>' +
        '<div style="font-size:12.5px;color:#475569">İş fotoğrafları: <b>' + (d.manual ? 'onayla görünür' : 'iş bitince ' + d.delay_min + ' dk sonra otomatik') + '</b> <button data-o="mode" style="' + B + ';margin-left:6px">' + (d.manual ? 'Otomatiğe al' : 'Elle onaya al') + '</button></div></div>';
      var sec = function (t, n, inner) { return n ? '<div class="spx-card"><b>' + t + ' (' + n + ')</b>' + inner + '</div>' : ''; };
      var av = function (src, nm, rd) { return '<a href="' + src + '" target="_blank" rel="noreferrer"><img src="' + src + '" alt="" style="width:84px;height:84px;object-fit:cover;' + (rd ? 'border-radius:50%;' : '') + 'border:2px solid #e2e8f0"></a>'; };
      h += sec('Usta profil fotoğrafları', d.ustalar.length, '<div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:8px">' + d.ustalar.map(function (u) {
        var src = location.origin + '/api/files/' + u.photo_path + '?auth=' + tk + '&v=' + encodeURIComponent(u.photo_at || '');
        return '<div style="width:120px;text-align:center">' + av(src, u.name, 1) + '<div style="font-weight:600;margin:4px 0">' + esc(u.name) + '</div><button data-o="uok" data-id="' + u.id + '" style="' + O + ';margin:0 4px 0 0">Onayla</button><button data-o="ured" data-id="' + u.id + '" style="' + B + ';margin:0">Reddet</button></div>'; }).join('') + '</div>');
      h += sec('Müşteri profil fotoğrafları', d.musteriler.length, '<div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:8px">' + d.musteriler.map(function (u) {
        return '<div style="width:120px;text-align:center">' + av(u.avatar, u.name, 1) + '<div style="font-weight:600;margin:4px 0">' + esc(u.name) + '</div><button data-o="mok" data-id="' + u.id + '" style="' + O + ';margin:0 4px 0 0">Onayla</button><button data-o="mred" data-id="' + u.id + '" style="' + B + ';margin:0">Reddet</button></div>'; }).join('') + '</div>');
      h += sec('Yorumlar', d.yorumlar.length, d.yorumlar.map(function (r) {
        return '<div style="border-top:1px solid #e2e8f0;padding:10px 0"><div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap"><b>' + esc(r.name || 'Müşteri') + '</b><span style="color:#ca8a04">' + '★'.repeat(r.rating || 0) + '<span style="color:#cbd5e1">' + '★'.repeat(5 - (r.rating || 0)) + '</span></span></div><div style="font-size:11.5px;color:#94a3b8">' + esc(r.job_number || '') + (r.brand ? ' · ' + esc(r.brand) : '') + ' · ' + esc(String(r.created_at || '').slice(0, 10)) + '</div><div style="margin:5px 0;white-space:pre-wrap">' + esc(r.comment) + '</div>' +
          '<button data-o="rok" data-id="' + r.id + '" style="' + O + '">Onayla</button><button data-o="rred" data-id="' + r.id + '" style="' + B + '">Gizle</button></div>'; }).join(''));
      h += sec('İş fotoğrafları (servis kayıtları)', d.isler.length, d.isler.map(function (j) {
        return '<div style="border-top:1px solid #e2e8f0;padding:8px 0;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap"><span><b>' + esc(j.job_number) + '</b> · ' + esc(j.customer || '') + ' · ' + esc(j.tech || '') + ' <span style="color:#64748b">(' + j.count + ' fotoğraf)</span></span><a href="/admin/jobs/' + j.job_id + '" style="color:#1155cc">Fotoğrafları incele →</a></div>'; }).join(''));
      if (!d.total) h += '<div class="spx-card" style="text-align:center;color:#64748b;padding:30px">✔ Onay bekleyen bir şey yok.</div>';
      var b = body(); if (!b || TAB !== 'onay') return; b.innerHTML = h;
      b.onclick = function (e) {
        var x = e.target.closest && e.target.closest('[data-o]'); if (!x) return; var a = x.getAttribute('data-o'), id = x.getAttribute('data-id'), p;
        if (a === 'mode') p = call('PUT', '/foto/ayar', { manual: !d.manual });
        else if (a === 'uok') p = call('POST', '/foto/usta/' + id, { state: 'ok' });
        else if (a === 'ured') { if (!confirm('Fotoğraf reddedilip kaldırılsın mı? Usta yenisini yükleyebilir.')) return; p = call('POST', '/foto/usta/' + id, { state: 'red' }); }
        else if (a === 'mok') p = call('POST', '/foto/musteri/' + id, { state: 'ok' });
        else if (a === 'mred') { if (!confirm('Müşteri fotoğrafı reddedilip kaldırılsın mı?')) return; p = call('POST', '/foto/musteri/' + id, { state: 'red' }); }
        else if (a === 'rok') p = call('PUT', '/reviews/' + id, { status: 'yayinda' });
        else if (a === 'rred') p = call('PUT', '/reviews/' + id, { status: 'gizli' });
        else return;
        x.disabled = true; p.then(function () { toast('Kaydedildi'); drawOnay(); }).catch(function (er) { fail(er); x.disabled = false; });
      };
    }).catch(fail);
  }
  /* ===== Musteri memnuniyeti / Usta borc vadesi / Gunun is haritasi ===== */
  function waLink(ph, txt) { var n = String(ph || '').replace(/\D/g, ''); if (n.indexOf('00') === 0) n = n.slice(2); if (n.charAt(0) === '0') n = '9' + n; else if (n.length === 10) n = '90' + n; return 'https://wa.me/' + n + '?text=' + encodeURIComponent(txt || ''); }
  var MEM_D = 90;
  function drawMemnun() {
    call('GET', '/reports/satisfaction?days=' + MEM_D).then(function (r) {
      var stars = function (v) { return '<b style="color:' + (v >= 4.5 ? '#15803d' : v >= 3.5 ? '#ca8a04' : '#dc2626') + '">' + v.toFixed(1) + ' ★</b>'; };
      var mx = Math.max.apply(null, [1].concat([1, 2, 3, 4, 5].map(function (k) { return r.dist[k]; })));
      var h = '<div class="spx-card"><b>Dönem</b> <select id="mm_d" style="margin-left:6px">' + [[7, 'Son 7 gün'], [30, 'Son 30 gün'], [90, 'Son 90 gün'], [365, 'Son 1 yıl']].map(function (x) { return '<option value="' + x[0] + '"' + (x[0] === r.days ? ' selected' : '') + '>' + x[1] + '</option>'; }).join('') + '</select></div>' +
        grid([stat('Ortalama puan', r.rated ? stars(r.avg) : '—', r.rated + ' değerlendirme'), stat('Tamamlanan iş', r.done, ''), stat('Puan veren oranı', '%' + r.response_rate, 'Puanlama mesajı açıksa artar'), stat('Düşük puan (1-2★)', '<span style="color:' + (r.low.length ? '#dc2626' : '#15803d') + '">' + r.low.length + '</span>', 'Aranması gerekenler')]) +
        '<div class="spx-card"><b>Puan dağılımı</b>' + [5, 4, 3, 2, 1].map(function (k) { return '<div style="display:flex;align-items:center;gap:8px;margin-top:6px"><span style="width:28px">' + k + '★</span><div style="flex:1;background:#e2e8f0;border-radius:6px;height:10px"><div style="width:' + (100 * r.dist[k] / mx) + '%;height:10px;border-radius:6px;background:' + (k >= 4 ? '#16a34a' : k === 3 ? '#f59e0b' : '#dc2626') + '"></div></div><span style="width:32px;text-align:right">' + r.dist[k] + '</span></div>'; }).join('') + '</div>';
      var rank = function (t, a) { return '<div class="spx-card"><b>' + t + '</b>' + tbl(['Ad', 'Ortalama', 'Adet'], a.slice(0, 15).map(function (x) { return tr_([esc(x.name), stars(x.avg), x.n]); })) + '</div>'; };
      h += rank('Usta bazında', r.techs) + rank('Marka bazında', r.brands) + rank('Cihaz türü bazında', r.devices);
      h += '<div class="spx-card"><b>Düşük puanlı işler — müşteriyi arayın</b>' + (r.low.length ? r.low.map(function (x) { return '<div style="border:1px solid #fecaca;background:#fef2f2;border-radius:12px;padding:10px;margin-top:8px"><div style="display:flex;justify-content:space-between;gap:8px"><b>' + esc(x.customer) + ' · ' + esc(x.job_number) + '</b><b style="color:#dc2626">' + x.rating + '★</b></div><small style="color:#64748b">' + esc(x.at) + ' · Usta: ' + esc(x.tech || '—') + '</small>' + (x.comment ? '<div style="margin-top:4px;font-size:13px">“' + esc(x.comment) + '”</div>' : '') + (x.phone ? '<div style="display:flex;gap:8px;margin-top:8px"><a class="spx-b" href="tel:' + esc(x.phone) + '" style="flex:1;text-align:center;text-decoration:none">📞 Ara</a><a class="spx-b" target="_blank" rel="noreferrer" href="' + waLink(x.phone, 'Merhaba ' + (x.customer || '').split(' ')[0] + ', ServisPlus servisimizden memnun kalmadığınızı gördük. Sorunu çözmek isteriz, size nasıl yardımcı olabiliriz?') + '" style="flex:1;text-align:center;text-decoration:none">💬 WhatsApp</a></div>' : '') + '</div>'; }).join('') : '<p style="color:#64748b">Bu dönemde düşük puan yok 🎉</p>') + '</div>';
      body().innerHTML = h; $('#mm_d').onchange = function () { MEM_D = +this.value; drawMemnun(); };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  /* ===== Rapor Merkezi: ozet / musteri yolculugu / usta / site / finans ===== */
  var RP = { t: 'ozet', d: 30, q: '', ch: '', sort: 'recent' };
  function rpNum(n) { return (+n || 0).toLocaleString('tr-TR', { maximumFractionDigits: 0 }); }
  function rpDelta(v) { if (v == null) return ''; var c = v > 0 ? '#15803d' : v < 0 ? '#dc2626' : '#64748b'; return ' <span style="font-size:11px;font-weight:700;color:' + c + '">' + (v > 0 ? '▲ ' : v < 0 ? '▼ ' : '') + Math.abs(v) + '%</span>'; }
  function rpK(l, v, sub, delta, col) { return '<div class="spx-card" style="margin:0;border-top:3px solid ' + (col || '#2563eb') + '"><small style="color:#64748b;font-weight:600">' + l + '</small><div class="spx-stat" style="font-size:24px">' + v + rpDelta(delta) + '</div>' + (sub ? '<small style="color:#64748b">' + sub + '</small>' : '') + '</div>'; }
  function rpBars(rows, key, col, h) {
    h = h || 110; if (!rows || !rows.length) return '<p style="color:#64748b">Veri yok</p>';
    var mx = Math.max.apply(null, [1].concat(rows.map(function (r) { return r[key] || 0; }))), w = 100 / rows.length;
    var step = rows.length > 16 ? Math.ceil(rows.length / 10) : 1;
    var s = '<svg viewBox="0 0 400 ' + (h + 18) + '" preserveAspectRatio="none" style="width:100%;height:' + (h + 18) + 'px;display:block">';
    rows.forEach(function (r, i) {
      var v = r[key] || 0, bh = Math.round(v / mx * h), x = i * 400 / rows.length, bw = Math.max(2, 400 / rows.length - 3);
      s += '<rect x="' + (x + 1.5).toFixed(1) + '" y="' + (h - bh) + '" width="' + bw.toFixed(1) + '" height="' + Math.max(bh, v ? 1 : 0) + '" rx="2" fill="' + col + '"><title>' + esc(r.label || r.name) + ': ' + rpNum(v) + '</title></rect>';
      if (i % step === 0) s += '<text x="' + (x + bw / 2).toFixed(1) + '" y="' + (h + 13) + '" font-size="9" text-anchor="' + (i === 0 ? 'start' : 'middle') + '" fill="#94a3b8">' + esc(r.label || r.name) + '</text>';
    });
    return s + '</svg>';
  }
  function rpList(rows, col, fmt, n) {
    rows = (rows || []).slice(0, n || 10); if (!rows.length) return '<p style="color:#64748b;margin:6px 0">Veri yok</p>';
    var mx = Math.max.apply(null, [1].concat(rows.map(function (r) { return r.value; })));
    return rows.map(function (r) { return '<div style="margin-top:7px"><div style="display:flex;justify-content:space-between;gap:8px;font-size:13px"><span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(r.name) + '</span><b>' + (fmt ? fmt(r.value) : rpNum(r.value)) + '</b></div><div style="height:6px;background:#e2e8f0;border-radius:4px;margin-top:3px"><div style="height:6px;width:' + Math.max(2, r.value / mx * 100) + '%;background:' + col + ';border-radius:4px"></div></div></div>'; }).join('');
  }
  function rpCard(t, inner, sub) { return '<div class="spx-card"><b>' + t + '</b>' + (sub ? '<small style="display:block;color:#64748b;margin-top:2px">' + sub + '</small>' : '') + '<div style="margin-top:6px">' + inner + '</div></div>'; }
  function rpTwo(a, b) { return '<div class="spx-g" style="grid-template-columns:repeat(auto-fit,minmax(280px,1fr));margin-bottom:14px;align-items:start">' + a + b + '</div>'; }
  function rpDl(path, name) {
    fetch(API + path, { headers: { Authorization: 'Bearer ' + LS.get('token', '') } }).then(function (r) { if (!r.ok) throw new Error('İndirilemedi'); return r.blob(); }).then(function (b) {
      var a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = name; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
    }).catch(fail);
  }
  function rpHead(csvPath, csvName) {
    var tabs = [['ozet', 'Genel Özet'], ['musteri', 'Müşteri Yolculuğu'], ['usta', 'Ustalar'], ['site', 'Site & Reklam'], ['finans', 'Finans']];
    var h = '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">' + tabs.map(function (x) { return '<button class="spx-b' + (RP.t === x[0] ? ' p' : '') + '" data-rt="' + x[0] + '">' + x[1] + '</button>'; }).join('') + '</div>';
    h += '<div class="spx-card" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><b>Dönem</b><select id="rp_d">' + [[7, 'Son 7 gün'], [30, 'Son 30 gün'], [90, 'Son 90 gün'], [180, 'Son 6 ay'], [365, 'Son 1 yıl']].map(function (x) { return '<option value="' + x[0] + '"' + (x[0] === RP.d ? ' selected' : '') + '>' + x[1] + '</option>'; }).join('') + '</select>' +
      (csvPath ? '<button class="spx-b" id="rp_csv" style="margin-left:auto">⬇ Excel (CSV) indir</button>' : '') + '</div>';
    return h;
  }
  function rpBind(csvPath, csvName) {
    var b = body();
    b.onclick = function (e) { var t = e.target.closest('[data-rt]'); if (t) { RP.t = t.getAttribute('data-rt'); drawRapor(); } };
    var d = $('#rp_d'); if (d) d.onchange = function () { RP.d = +this.value; drawRapor(); };
    var c = $('#rp_csv'); if (c) c.onclick = function () { rpDl(csvPath, csvName); };
  }
  /* G177: Kurulum durumu — eksik ayarlar listesi (salt okunur, gizli değer göstermez) */
  function drawKurulum() {
    call('GET', '/admin/kurulum').then(function (r) {
      var lv = { 'kritik': ['#fee2e2', '#991b1b'], 'önerilir': ['#fef3c7', '#92400e'], 'isteğe bağlı': ['#e2e8f0', '#334155'] };
      var nm = { 'ek:wa': 'WhatsApp & Bildirim', 'ek:moduller': 'Aç/Kapat & Entegrasyonlar', 'ek:gsc': 'Google Search Console', '/admin/growth': 'Büyüme', '/admin/marketing': 'Pazarlama' };
      var ok = r.items.filter(function (x) { return x.ok; }).length;
      var h = '<div class="spx-card" style="display:flex;gap:14px;align-items:center;flex-wrap:wrap"><div style="font-size:30px;font-weight:800;color:' + (r.missing ? (r.critical ? '#dc2626' : '#d97706') : '#16a34a') + '">' + ok + ' / ' + r.items.length + '</div><div><b>' +
        (r.missing ? r.missing + ' ayar eksik' + (r.critical ? ' · ' + r.critical + ' tanesi kritik' : '') : 'Tüm ayarlar tamam') + '</b><small style="display:block;color:#64748b">Bu liste yalnızca ayarın dolu olup olmadığını gösterir; şifre ve anahtarlar burada görünmez. “Ayarla” ile ilgili sayfaya gidin.</small></div></div>';
      h += '<div class="spx-card">' + r.items.map(function (x) {
        var c = lv[x.level] || lv['isteğe bağlı'];
        return '<div class="spx-row spx-kwr" style="align-items:flex-start;gap:10px"><div style="flex:none;width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;color:#fff;background:' + (x.ok ? '#16a34a' : (x.level === 'kritik' ? '#dc2626' : '#d97706')) + '">' + (x.ok ? '✓' : '!') + '</div>' +
          '<div class="t" style="flex:1"><b>' + esc(x.label) + '</b> <span class="spx-pill" style="background:' + c[0] + ';color:' + c[1] + '">' + esc(x.level) + '</span><small style="display:block;color:#64748b;margin-top:3px">' + esc(x.desc) + '</small></div>' +
          '<button class="spx-b' + (x.ok ? '' : ' p') + '" data-kw="' + esc(x.where) + '" style="flex:none">' + (x.ok ? 'Aç' : 'Ayarla') + ' · ' + esc(nm[x.where] || '') + '</button></div>';
      }).join('') + '</div>';
      if (r.server_side && r.server_side.length) h += '<div class="spx-card" style="background:#f8fafc"><b>Sunucu tarafında</b>' + r.server_side.map(function (t) { return '<small style="display:block;color:#64748b;margin-top:4px">' + esc(t) + '</small>'; }).join('') + '</div>';
      if (!document.getElementById('spx-kw-css')) { var st = document.createElement('style'); st.id = 'spx-kw-css'; st.textContent = '@media(max-width:640px){.spx-kwr{flex-wrap:wrap}.spx-kwr>.t{flex:1 1 calc(100% - 40px)!important;min-width:0}.spx-kwr>button{margin-left:36px;white-space:normal;text-align:left}}'; document.head.appendChild(st); }
      body().innerHTML = h;
      body().onclick = function (e) {
        var b = e.target.closest('[data-kw]'); if (!b) return; var w = b.getAttribute('data-kw');
        if (w.indexOf('ek:') === 0) { TAB = w.slice(3); draw(); markActive(); }
        else { ov.classList.remove('on'); markActive(); try { history.pushState({}, '', w); window.dispatchEvent(new PopStateEvent('popstate', { state: {} })); } catch (er) { location.href = w; } }
      };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  function drawRapor() {
    var fnm = { ozet: rpOzet, musteri: rpMusteri, usta: rpUsta, site: rpSite, finans: rpFinans }[RP.t];
    fnm();
  }
  function rpErr(e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; }
  function rpOzet() {
    call('GET', '/rapor/ozet?days=' + RP.d).then(function (r) {
      var a = r.jobs, c = r.chg, s = r.site, f = r.funnel, h = rpHead();
      h += '<div class="spx-g" style="margin-bottom:14px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">' + [rpK('Servis kaydı', rpNum(a.jobs), a.open + ' açık · ' + a.cancel + ' iptal', c.jobs, '#2563eb'), rpK('Tamamlanan', rpNum(a.done), 'Tamamlama %' + a.done_rate, c.done, '#16a34a'),
        rpK('Ciro', TLf(a.revenue), 'Ort. fiş ' + TLf(a.avg_ticket), c.revenue, '#0891b2'), rpK('Yeni müşteri', rpNum(r.customers.new), 'Tekrar gelen: ' + r.customers.repeat, c.customers, '#7c3aed'),
        rpK('Müşteri puanı', a.rating ? a.rating.toFixed(2) + ' ★' : '—', a.rating_n + ' değerlendirme', null, '#ca8a04'), rpK('Ort. tamamlama', a.avg_hours != null ? a.avg_hours + ' sa' : '—', 'Kayıttan bitişe', null, '#64748b'),
        rpK('Site oturumu', rpNum(s.sessions), rpNum(s.pageviews) + ' sayfa', c.sessions, '#ea580c'), rpK('Talep', rpNum(s.leads), 'Arama ' + s.calls + ' · WhatsApp ' + s.whatsapp, c.leads, '#db2777')].join('') + '</div>';
      var top = Math.max(1, f[0].value);
      h += rpCard('Dönüşüm hunisi', f.map(function (x, i) { var p = i ? (f[i - 1].value ? Math.min(100, Math.round(x.value * 100 / f[i - 1].value)) : 0) : 100; return '<div style="margin-top:8px"><div style="display:flex;justify-content:space-between;font-size:13px"><span>' + esc(x.name) + '</span><b>' + rpNum(x.value) + ((i === 3 || (i === 1 && f[0].value)) ? ' <small style="color:#64748b">(%' + p + ')</small>' : '') + '</b></div><div style="height:10px;background:#e2e8f0;border-radius:6px;margin-top:3px"><div style="height:10px;width:' + Math.max(2, Math.min(100, x.value * 100 / Math.max(top, f[2].value, 1))) + '%;background:' + ['#ea580c', '#db2777', '#2563eb', '#16a34a'][i] + ';border-radius:6px"></div></div></div>'; }).join(''), 'Site → talep → servis kaydı → tamamlanan. Telefonla gelenler servis kaydı adımında görünür.');
      h += rpTwo(rpCard('Günlük servis kaydı', rpBars(r.daily, 'jobs', '#2563eb')), rpCard('Günlük ciro (₺)', rpBars(r.daily, 'revenue', '#0891b2')));
      h += rpTwo(rpCard('Günlük site oturumu', rpBars(r.daily, 'sessions', '#ea580c')), rpCard('Günlük talep', rpBars(r.daily, 'leads', '#db2777')));
      h += rpTwo(rpCard('Müşteri nereden geldi (servis kaydı)', rpList(r.channels, '#7c3aed')), rpCard('Servis durumu', rpList(r.status.map(function (x) { return { name: ({ yeni: 'Yeni', atandi: 'Atandı', yolda: 'Yolda', basladi: 'Başladı', tamamlandi: 'Tamamlandı', faturalandi: 'Faturalandı', iptal: 'İptal' })[x.name] || x.name, value: x.value }; }), '#64748b')));
      h += rpTwo(rpCard('Cihaz türü', rpList(r.devices, '#16a34a')), rpCard('Marka', rpList(r.brands, '#0ea5e9')));
      h += rpTwo(rpCard('İl bazında servis', rpList(r.cities, '#2563eb', null, 10)), rpCard('İl / ilçe (en yoğun)', rpList(r.districts, '#f59e0b', null, 12)));
      body().innerHTML = h; rpBind();
    }).catch(rpErr);
  }
  function rpMusteri() {
    call('GET', '/rapor/musteri?days=' + RP.d + '&sort=' + RP.sort + '&limit=400' + (RP.q ? '&q=' + encodeURIComponent(RP.q) : '') + (RP.ch ? '&channel=' + encodeURIComponent(RP.ch) : '')).then(function (r) {
      var sm = r.summary, h = rpHead();
      h += '<div class="spx-g" style="margin-bottom:14px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">' + [rpK('Müşteri', rpNum(r.total), 'Dönemde hareketli', null, '#7c3aed'), rpK('Site izlenen', rpNum(sm.tracked), 'Ziyaret verisi olan', null, '#ea580c'), rpK('Servis alan', rpNum(sm.with_job), '', null, '#2563eb'), rpK('Ciro', TLf(sm.revenue), '', null, '#16a34a'), rpK('Ort. giriş günü', sm.avg_visit_days, 'İzlenen müşteri başına', null, '#0891b2')].join('') + '</div>';
      h += '<div class="spx-card" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><input id="rm_q" placeholder="Ad, telefon, il veya ilçe ara" value="' + esc(RP.q) + '" style="flex:1;min-width:180px"><select id="rm_s"><option value="recent"' + (RP.sort === 'recent' ? ' selected' : '') + '>En son hareket</option><option value="revenue"' + (RP.sort === 'revenue' ? ' selected' : '') + '>En yüksek ciro</option></select><button class="spx-b p" id="rm_go">Ara</button><button class="spx-b" id="rp_csv">⬇ Excel (CSV) indir</button></div>';
      h += rpCard('Kanallara göre müşteri', r.channels.length ? '<div style="display:flex;gap:6px;flex-wrap:wrap">' + r.channels.map(function (x) { return '<span class="spx-pill" style="cursor:pointer">' + esc(x.name) + ' · ' + x.value + '</span>'; }).join('') + '</div>' : '<p style="color:#64748b">Veri yok</p>');
      h += '<div class="spx-card"><b>Müşteri yolculuğu</b> <small style="color:#64748b">(' + r.shown + ' / ' + r.total + ' gösteriliyor)</small>' + tbl(['Müşteri', 'Bölge', 'İlk temas', 'Nereden / nasıl', 'Kaynak · kampanya · kelime', 'İlk sayfa', 'Cihaz', 'Giriş', 'Tık', 'Servis', 'Ciro', 'Puan'], r.rows.map(function (x) {
        var lines = [x.channel_label + (x.how ? ' <small style="color:#64748b">· ' + esc(x.how) + '</small>' : '')];
        var src = [x.source, x.campaign, x.term].filter(Boolean).map(esc).join(' · ');
        return tr_(['<b>' + esc(x.name || '—') + '</b><br><small style="color:#64748b">' + esc(x.phone || '') + '</small>', esc([x.city, x.district].filter(Boolean).join(' / ') || '—'), esc(x.first_contact || '—'), lines.join(''), src || '—', esc(x.landing || '—'), esc(x.device || '—'),
          x.sessions ? '<b>' + x.visit_days + '</b> gün<br><small style="color:#64748b">' + x.pageviews + ' sayfa · ' + x.sessions + ' oturum</small>' : '<small style="color:#94a3b8">izlenmedi</small>', (x.calls || x.whatsapp || x.forms) ? '📞' + x.calls + ' 💬' + x.whatsapp + ' 📝' + x.forms : '—',
          x.jobs ? x.done + '/' + x.jobs : '—', x.revenue ? TLf(x.revenue) : '—', x.rating ? x.rating + ' ★' : '—']);
      })) + '<small style="display:block;color:#64748b;margin-top:8px">' + esc(r.note) + '</small></div>';
      body().innerHTML = h; rpBind('/rapor/musteri?days=' + RP.d + '&fmt=csv&limit=3000' + (RP.q ? '&q=' + encodeURIComponent(RP.q) : ''), 'musteri-yolculugu.csv');
      var go = function () { RP.q = $('#rm_q').value.trim(); RP.sort = $('#rm_s').value; rpMusteri(); };
      $('#rm_go').onclick = go; $('#rm_q').onkeydown = function (e) { if (e.key === 'Enter') go(); }; $('#rm_s').onchange = go;
    }).catch(rpErr);
  }
  function rpUsta() {
    call('GET', '/rapor/usta?days=' + RP.d).then(function (r) {
      var sm = r.summary, h = rpHead('/rapor/usta?days=' + RP.d + '&fmt=csv', 'usta-raporu.csv');
      h += '<div class="spx-g" style="margin-bottom:14px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">' + [rpK('Usta', sm.techs, sm.active_in_period + ' tanesi dönemde iş yaptı', null, '#0ea5e9'), rpK('Atanan iş', rpNum(sm.jobs), sm.unassigned + ' atanmamış', null, '#2563eb'), rpK('Ciro', TLf(sm.revenue), '', null, '#16a34a'), rpK('Ustaların şirkete borcu', TLf(sm.total_debt), '', null, '#dc2626')].join('') + '</div>';
      var rows = r.rows.filter(function (x) { return x.jobs || x.id; });
      h += rpTwo(rpCard('Ciroya göre usta', rpList(rows.map(function (x) { return { name: x.name, value: x.revenue }; }).filter(function (x) { return x.value; }), '#16a34a', TLf, 10)), rpCard('Tamamlanan işe göre usta', rpList(rows.map(function (x) { return { name: x.name, value: x.done }; }).filter(function (x) { return x.value; }), '#2563eb', null, 10)));
      h += '<div class="spx-card"><b>Usta performans tablosu</b>' + tbl(['Usta', 'Atanan', 'Biten', 'İptal', 'Açık', 'Biten %', 'Ciro', 'Ort. fiş', 'Ort. süre', 'Puan', 'Düşük', 'Usta payı', 'Borç', 'En çok', 'Bölge'], rows.map(function (x) {
        return tr_(['<b>' + esc(x.name) + '</b>' + (x.active ? '' : ' <small style="color:#dc2626">pasif</small>'), x.jobs, x.done, x.cancel, x.open, '%' + x.done_rate, TLf(x.revenue), x.avg_ticket ? TLf(x.avg_ticket) : '—', x.avg_hours != null ? x.avg_hours + ' sa' : '—',
          x.rating ? '<b style="color:' + (x.rating >= 4.5 ? '#15803d' : x.rating >= 3.5 ? '#ca8a04' : '#dc2626') + '">' + x.rating + ' ★</b> <small>(' + x.rating_n + ')</small>' : '—', x.low || '—', TLf(x.share), x.debt ? '<b style="color:#dc2626">' + TLf(x.debt) + '</b>' : '—', esc(x.top_device || '—'), esc(x.top_city || '—')]);
      })) + '</div>';
      body().innerHTML = h; rpBind('/rapor/usta?days=' + RP.d + '&fmt=csv', 'usta-raporu.csv');
    }).catch(rpErr);
  }
  function rpSite() {
    call('GET', '/rapor/site?days=' + RP.d).then(function (r) {
      var k = r.kpi, h = rpHead('/rapor/site?days=' + RP.d + '&fmt=csv', 'site-kanallar.csv');
      h += '<div class="spx-g" style="margin-bottom:14px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">' + [rpK('Oturum', rpNum(k.sessions), rpNum(k.visitors) + ' ziyaretçi', null, '#ea580c'), rpK('Sayfa görüntüleme', rpNum(k.pageviews), 'Tekrar giren: ' + k.returning, null, '#2563eb'), rpK('Dönüşüm', '%' + k.conv_rate, 'Arama / WhatsApp / form', null, '#16a34a'),
        rpK('Hemen çıkış', '%' + k.bounce_rate, 'Ort. süre ' + k.avg_duration + ' sn', null, '#64748b'), rpK('Arama tıklama', rpNum(k.calls), '', null, '#0891b2'), rpK('WhatsApp tıklama', rpNum(k.whatsapp), '', null, '#16a34a'), rpK('Form talebi', rpNum(k.leads), '', null, '#db2777')].join('') + '</div>';
      h += '<div class="spx-card"><b>Kanal performansı (reklam ve kaynak)</b>' + tbl(['Kanal', 'Oturum', 'Sayfa', 'Arama', 'WhatsApp', 'Form', 'Dönüşüm', 'Çıkış', 'Süre', 'Servis', 'Biten', 'Ciro'], r.channels.map(function (x) {
        return tr_(['<b>' + esc(x.label) + '</b>', rpNum(x.sessions), rpNum(x.pageviews), x.calls, x.whatsapp, x.forms, '%' + x.conv_rate, '%' + x.bounce_rate, x.avg_duration + ' sn', x.jobs, x.done, x.revenue ? TLf(x.revenue) : '—']);
      })) + '</div>';
      h += rpTwo(rpCard('Kaynak (site / platform)', rpList(r.sources, '#ea580c')), rpCard('Yönlendiren siteler', rpList(r.referrers, '#7c3aed')));
      h += rpTwo(rpCard('Reklam kampanyaları', rpList(r.campaigns, '#db2777')), rpCard('Google anahtar kelimeleri', rpList(r.terms, '#2563eb', null, 15)));
      h += rpCard('İlk giriş sayfaları', tbl(['Sayfa', 'Oturum', 'Dönüşen', 'Oran'], r.landing.map(function (x) { return tr_([esc(x.name), x.sessions, x.conv, '%' + x.rate]); })));
      h += rpTwo(rpCard('En çok görüntülenen sayfa', rpList(r.top_pages, '#0891b2', null, 15)), rpCard('Siteden gelen taleplerde en çok ilçe', rpList(r.lead_districts, '#f59e0b', null, 15)));
      h += rpTwo(rpCard('Saate göre ziyaret', rpBars(r.hourly, 'value', '#ea580c')), rpCard('Güne göre ziyaret', rpBars(r.weekday, 'value', '#2563eb')));
      h += rpTwo(rpCard('Cihaz', rpList(r.devices, '#0ea5e9')), rpCard('Tarayıcı / sistem', rpList(r.browsers.concat(r.os), '#64748b', null, 10)));
      h += rpTwo(rpCard('Talep edilen hizmet', rpList(r.lead_services, '#16a34a')), rpCard('Talep edilen marka', rpList(r.lead_brands, '#7c3aed')));
      h += rpTwo(rpCard('Site içi aramalar', rpList(r.site_search.top, '#2563eb', null, 12), r.site_search.total + ' arama'), rpCard('Sonuç bulunamayan aramalar', rpList(r.site_search.zero, '#dc2626', null, 12), 'İçerik/ürün eksiği ipucu'));
      h += '<small style="color:#64748b">' + esc(r.note) + '</small>';
      body().innerHTML = h; rpBind('/rapor/site?days=' + RP.d + '&fmt=csv', 'site-kanallar.csv');
    }).catch(rpErr);
  }
  function rpFinans() {
    call('GET', '/rapor/finans?days=' + RP.d).then(function (r) {
      var k = r.kpi, h = rpHead();
      h += '<div class="spx-g" style="margin-bottom:14px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">' + [rpK('Gelir (kasa)', TLf(k.income), '', null, '#16a34a'), rpK('Gider', TLf(k.expense), '', null, '#dc2626'), rpK('Net', '<span style="color:' + (k.net >= 0 ? '#15803d' : '#dc2626') + '">' + TLf(k.net) + '</span>', '', null, '#2563eb'), rpK('İş cirosu', TLf(k.job_revenue), k.done + ' tamamlanan · ort. ' + TLf(k.avg_ticket), null, '#0891b2'),
        rpK('Tahsil edilen', TLf(k.collected), '', null, '#16a34a'), rpK('Tahsil edilecek', TLf(k.receivable), 'Veresiye / eksik', null, '#f59e0b'), rpK('Usta payı', TLf(k.tech_share), '', null, '#7c3aed')].join('') + '</div>';
      h += rpTwo(rpCard('Aylık gelir', rpBars(r.monthly.map(function (m) { return { name: m.name, value: m.gelir }; }), 'value', '#16a34a')), rpCard('Aylık gider', rpBars(r.monthly.map(function (m) { return { name: m.name, value: m.gider }; }), 'value', '#dc2626')));
      h += rpTwo(rpCard('Gider kalemleri', rpList(r.expense_cats, '#dc2626', TLf)), rpCard('Ödeme yöntemi', rpList(r.pay_methods, '#16a34a', TLf)));
      h += rpTwo(rpCard('Cihaz türüne göre ciro', rpList(r.by_device, '#2563eb', TLf)), rpCard('İle göre ciro', rpList(r.by_city, '#0891b2', TLf)));
      h += rpCard('Tahsil edilecekler (veresiye)', tbl(['Kayıt', 'Müşteri', 'Usta', 'Tarih', 'Tutar'], r.receivables.map(function (x) { return tr_([esc(x.job || ''), esc(x.customer || ''), esc(x.tech || '—'), esc(x.date), '<b>' + TLf(x.amount) + '</b>']); })));
      body().innerHTML = h; rpBind();
    }).catch(rpErr);
  }
  /* --- Canli Sohbet: site ziyaretcileriyle karsilikli sohbet (ziyaretci mesajlari admin bildirimiyle gelir) --- */
  var CHAT_SEL = null, CHAT_T = null;
  function shNarrow() { return window.innerWidth < 760; }
  function shLayout() {
    var l = document.getElementById('sh-list'), m = document.getElementById('sh-main'), w = document.getElementById('sh-wrap'); if (!l || !m || !w) return;
    if (shNarrow()) { w.style.display = 'block'; l.style.display = CHAT_SEL ? 'none' : 'block'; m.style.display = CHAT_SEL ? 'flex' : 'none'; }
    else { w.style.display = 'grid'; w.style.gridTemplateColumns = '260px 1fr'; l.style.display = 'block'; m.style.display = 'flex'; }
  }
  var CHAT_Q = '', CHAT_F = 'all', CHAT_ITEMS = [], CHAT_UNREAD = null;
  function chatBeep() {
    if (LS.get('spx_chat_snd', '1') !== '1') return;
    try { var A = window.AudioContext || window.webkitAudioContext, x = new A(), o = x.createOscillator(), g = x.createGain(); o.type = 'sine'; o.frequency.value = 880; g.gain.setValueAtTime(0.0001, x.currentTime); g.gain.exponentialRampToValueAtTime(0.25, x.currentTime + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, x.currentTime + 0.35); o.connect(g); g.connect(x.destination); o.start(); o.stop(x.currentTime + 0.4); o.onended = function () { x.close(); }; } catch (e) { }
  }
  function shAgo(iso) {
    var t = Date.parse(iso); if (!t) return ''; var d = Math.floor((Date.now() - t) / 1000);
    if (d < 60) return 'şimdi'; if (d < 3600) return Math.floor(d / 60) + ' dk'; if (d < 86400) return Math.floor(d / 3600) + ' sa'; return Math.floor(d / 86400) + ' gün';
  }
  function drawSohbet() {
    var chip = function (k, t) { return '<button type="button" class="spx-b" data-cf="' + k + '" style="padding:4px 9px;font-size:12px">' + t + '</button>'; };
    body().innerHTML = '<div id="sh-wrap" style="display:grid;grid-template-columns:260px 1fr;gap:12px;min-height:420px"><div id="sh-list" class="spx-card" style="padding:8px;max-height:70vh;overflow:auto"><div id="sh-tools" style="position:sticky;top:0;background:#fff;padding-bottom:6px;z-index:1"><input id="sh-q" type="search" placeholder="Ara: ad, telefon, mesaj…" value="' + esc(CHAT_Q) + '" style="width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:7px 9px;font-size:13px"><div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:6px">' + chip('all', 'Tümü') + chip('unread', 'Okunmamış') + chip('open', 'Açık') + chip('closed', 'Kapalı') + '<button type="button" class="spx-b" id="sh-snd" style="padding:4px 9px;font-size:12px;margin-left:auto"></button></div></div><div id="sh-items"></div></div><div id="sh-main" class="spx-card" style="padding:12px;display:flex;flex-direction:column;gap:8px"><p style="color:#64748b">Soldan bir sohbet seçin.</p></div></div>';
    shLayout();
    var q = document.getElementById('sh-q'); q.oninput = function () { CHAT_Q = q.value; renderChatList(); };
    var snd = document.getElementById('sh-snd'), paintSnd = function () { snd.textContent = LS.get('spx_chat_snd', '1') === '1' ? '🔔 Ses açık' : '🔕 Ses kapalı'; }; paintSnd();
    snd.onclick = function () { LS.set('spx_chat_snd', LS.get('spx_chat_snd', '1') === '1' ? '0' : '1'); paintSnd(); chatBeep(); };
    Array.prototype.forEach.call(document.querySelectorAll('#sh-tools [data-cf]'), function (b) { b.onclick = function () { CHAT_F = b.getAttribute('data-cf'); renderChatList(); }; });
    CHAT_UNREAD = null;
    loadChats();
    if (CHAT_SEL) loadChat(CHAT_SEL);
    clearInterval(CHAT_T);
    CHAT_T = setInterval(function () { if (TAB !== 'sohbet' || !document.getElementById('sh-list')) { clearInterval(CHAT_T); return; } loadChats(); if (CHAT_SEL && !document.hidden) loadChat(CHAT_SEL, true); }, 3000);
  }
  function renderChatList() {
    var el = document.getElementById('sh-items'); if (!el) return;
    Array.prototype.forEach.call(document.querySelectorAll('#sh-tools [data-cf]'), function (b) { var on = b.getAttribute('data-cf') === CHAT_F; b.style.background = on ? '#1155cc' : ''; b.style.color = on ? '#fff' : ''; });
    var q = CHAT_Q.trim().toLocaleLowerCase('tr');
    var rows = CHAT_ITEMS.filter(function (c) {
      if (CHAT_F === 'unread' && !c.unread_admin) return false;
      if (CHAT_F === 'open' && c.status === 'kapali') return false;
      if (CHAT_F === 'closed' && c.status !== 'kapali') return false;
      return !q || [c.name, c.phone, c.brand, c.last_text].join(' ').toLocaleLowerCase('tr').indexOf(q) >= 0;
    });
    el.innerHTML = rows.length ? rows.map(function (c) {
      var on = c.id === CHAT_SEL ? 'background:#eef4ff;' : '';
      var badge = c.unread_admin ? '<span style="background:#dc2626;color:#fff;border-radius:999px;padding:1px 7px;font-size:11px;margin-left:6px">' + c.unread_admin + '</span>' : '';
      var dot = '<span title="' + (c.online ? 'çevrimiçi' : 'çevrimdışı') + '" style="display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;background:' + (c.online ? '#16a34a' : '#cbd5e1') + '"></span>';
      return '<div data-cid="' + esc(c.id) + '" style="cursor:pointer;padding:10px;border-bottom:1px solid #e2e8f0;border-radius:8px;' + on + '"><div style="display:flex;justify-content:space-between;gap:6px"><span>' + dot + '<b>' + esc(c.name) + '</b>' + badge + '</span><small style="color:#94a3b8;white-space:nowrap">' + esc(shAgo(c.updated_at)) + '</small></div><div style="font-size:12px;color:#64748b">' + esc(c.phone) + (c.brand ? ' · ' + esc(c.brand) : '') + '</div><div style="font-size:12px;color:#334155;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + esc(c.last_text || '') + '</div>' + (c.status === 'kapali' ? '<small style="color:#94a3b8">kapalı</small>' : '') + '</div>';
    }).join('') : '<p style="color:#64748b;padding:8px">' + (CHAT_ITEMS.length ? 'Bu filtreyle sohbet yok.' : 'Henüz canlı sohbet yok.') + '</p>';
    Array.prototype.forEach.call(el.querySelectorAll('[data-cid]'), function (d) { d.onclick = function () { CHAT_SEL = d.getAttribute('data-cid'); shLayout(); renderChatList(); loadChat(CHAT_SEL); }; });
  }
  function loadChats() {
    call('GET', '/admin/chat/list').then(function (r) {
      CHAT_ITEMS = r.items || [];
      var un = CHAT_ITEMS.reduce(function (a, c) { return a + (c.unread_admin || 0); }, 0);
      if (CHAT_UNREAD !== null && un > CHAT_UNREAD) chatBeep();
      CHAT_UNREAD = un;
      renderChatList();
    }).catch(function (e) { var el2 = document.getElementById('sh-items'); if (el2) el2.innerHTML = '<p style="color:#dc2626;padding:8px">Sohbetler yüklenemedi: ' + esc((e && e.message) || 'bağlantı hatası') + '. Panel güncel değilse Python uygulamasını yeniden başlatın.</p>'; });
  }
  /* --- Hazir mesaj secici: "Otomatik cevap gönder" -> liste, birini secip gonder / yaziya aktar / duzenle --- */
  var QR = { open: false, items: null, form: null };
  function qrLoad(cb) { call('GET', '/admin/chat/quick-replies').then(function (r) { QR.items = r.items || []; if (cb) cb(); }).catch(function (e) { QR.open = false; alert(e && e.message ? e.message : 'Hazır mesajlar yüklenemedi'); }); }
  function qrFill(t, c) { return String(t || '').replace(/\{ad\}/g, ((c && c.name) || '').trim().split(' ')[0]); }
  function qrDraw(m, c, cid, fail) {
    var box = m.querySelector('#sh-qr'); if (!box) return;
    if (!QR.open) { box.style.display = 'none'; box.innerHTML = ''; return; }
    box.style.cssText = 'position:fixed;inset:0;z-index:100000;background:rgba(15,23,42,.5);display:flex;align-items:center;justify-content:center;padding:14px';
    var wrap = function (inner) { return '<div style="background:#fff;border-radius:14px;width:100%;max-width:520px;max-height:85vh;overflow:auto;padding:14px;box-shadow:0 20px 50px rgba(0,0,0,.3)">' + inner + '</div>'; };
    if (!QR.items) { box.innerHTML = wrap('<small style="color:#64748b">Hazır mesajlar yükleniyor…</small>'); qrLoad(function () { qrDraw(m, c, cid, fail); }); return; }
    var fld = 'border:1px solid #cbd5e1;border-radius:8px;padding:8px;font-size:13px;width:100%;box-sizing:border-box;margin-top:6px';
    var h = '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px"><b>Göndermek istediğiniz mesajı seçin</b><button class="spx-b" type="button" data-qr="x">Kapat</button></div>';
    h += QR.items.length ? QR.items.map(function (q, i) {
      return '<div style="border:1px solid #e2e8f0;border-radius:10px;padding:8px;margin-bottom:6px;background:#f8fafc"><b style="font-size:13px">' + esc(q.title) + '</b><div style="font-size:12px;color:#475569;margin:4px 0 6px;white-space:pre-wrap">' + esc(qrFill(q.text, c)) + '</div><div style="display:flex;gap:6px;flex-wrap:wrap"><button class="spx-b p" type="button" data-qr="send" data-i="' + i + '">Gönder</button><button class="spx-b" type="button" data-qr="fill" data-i="' + i + '">Yazıya aktar</button><button class="spx-b" type="button" data-qr="edit" data-i="' + i + '">Düzenle</button><button class="spx-b" type="button" data-qr="del" data-i="' + i + '">Sil</button></div></div>';
    }).join('') : '<p style="color:#64748b;margin:4px 0">Hazır mesaj yok. Aşağıdan ekleyin.</p>';
    if (QR.form) {
      h += '<div style="border:1px dashed #94a3b8;border-radius:10px;padding:8px;background:#fff"><b style="font-size:13px">' + (QR.form.id ? 'Hazır mesajı düzenle' : 'Yeni hazır mesaj') + '</b><input id="qr-t" maxlength="60" placeholder="Başlık (örn. Randevu saati sor)" value="' + esc(QR.form.title) + '" style="' + fld + '"><textarea id="qr-m" rows="3" maxlength="1000" placeholder="Mesaj metni" style="' + fld + '">' + esc(QR.form.text) + '</textarea><small style="color:#64748b;display:block;margin-top:4px">{ad} yazarsanız müşterinin adı otomatik gelir.</small><div style="display:flex;gap:6px;margin-top:6px"><button class="spx-b p" type="button" data-qr="save">Kaydet</button><button class="spx-b" type="button" data-qr="cancel">Vazgeç</button></div></div>';
    } else {
      h += '<button class="spx-b" type="button" data-qr="new">+ Yeni hazır mesaj</button>';
    }
    box.innerHTML = wrap(h);
    var ti = box.querySelector('#qr-t'), mi = box.querySelector('#qr-m');
    if (ti) ti.oninput = function () { QR.form.title = ti.value; };
    if (mi) mi.oninput = function () { QR.form.text = mi.value; };
    box.onclick = function (e) {
      if (e.target === box) { QR.open = false; QR.form = null; qrDraw(m, c, cid, fail); return; }
      var b = e.target.closest('[data-qr]'); if (!b) return;
      var act = b.getAttribute('data-qr'), q = QR.items[parseInt(b.getAttribute('data-i'), 10)];
      var again = function () { qrLoad(function () { qrDraw(m, c, cid, fail); }); };
      if (act === 'x') { QR.open = false; QR.form = null; qrDraw(m, c, cid, fail); }
      else if (act === 'new') { QR.form = { id: '', title: '', text: '' }; qrDraw(m, c, cid, fail); }
      else if (act === 'cancel') { QR.form = null; qrDraw(m, c, cid, fail); }
      else if (act === 'edit' && q) { QR.form = { id: q.id, title: q.title, text: q.text }; qrDraw(m, c, cid, fail); }
      else if (act === 'fill' && q) { var inp = m.querySelector('#sh-txt'); inp.value = qrFill(q.text, c); QR.open = false; qrDraw(m, c, cid, fail); inp.focus(); }
      else if (act === 'send' && q) { QR.open = false; call('POST', '/admin/chat/' + encodeURIComponent(cid) + '/reply', { text: qrFill(q.text, c) }).then(function () { loadChat(cid); loadChats(); }).catch(fail); }
      else if (act === 'del' && q) { if (!confirm('"' + q.title + '" hazır mesajı silinsin mi?')) return; call('DELETE', '/admin/chat/quick-replies/' + encodeURIComponent(q.id)).then(again).catch(fail); }
      else if (act === 'save') {
        var f = QR.form || {}, t = (f.title || '').trim(), x = (f.text || '').trim(); if (!t || !x) { alert('Başlık ve mesaj yazın'); return; }
        call(f.id ? 'PUT' : 'POST', '/admin/chat/quick-replies' + (f.id ? '/' + encodeURIComponent(f.id) : ''), { title: t, text: x }).then(function () { QR.form = null; again(); }).catch(fail);
      }
    };
  }
  function loadChat(cid, quiet) {
    call('GET', '/admin/chat/' + encodeURIComponent(cid)).then(function (r) {
      var m = document.getElementById('sh-main'); if (!m) return;
      var c = r.chat, draft = (m.querySelector('#sh-txt') || {}).value || '';
      var tyEl = m.querySelector('#sh-typing'); if (tyEl) tyEl.textContent = c.visitor_typing ? ((c.name || '').trim().split(' ')[0] + ' yazıyor…') : '';
      var prEl = m.querySelector('#sh-pres'); if (prEl) { prEl.textContent = c.online ? '● çevrimiçi' : '○ çevrimdışı'; prEl.style.color = c.online ? '#16a34a' : '#94a3b8'; }
      var sig = cid + ':' + r.messages.length + ':' + c.status + ':' + (c.visitor_seen_at || '');
      if (quiet && m.__sig === sig) return;
      var typing = document.activeElement && document.activeElement.id === 'sh-txt';
      var msgs = r.messages.map(function (x) {
        var mine = x.from === 'admin' || x.from === 'bot';
        var lab = x.from === 'visitor' ? esc(c.name) : (x.from === 'bot' ? 'Otomatik karşılama' : 'Temsilci');
        return '<div style="max-width:80%;padding:8px 10px;border-radius:12px;font-size:13px;margin:4px 0;' + (mine ? 'background:#1155cc;color:#fff;margin-left:auto' : 'background:#f1f5f9') + '"><small style="opacity:.75">' + lab + ' · ' + esc(new Date(x.at).toLocaleString('tr-TR')) + (mine && x.from === 'admin' ? ' · ' + ((c.visitor_seen_at && x.at <= c.visitor_seen_at) ? '✓✓ okundu' : '✓ iletildi') : '') + '</small><div>' + esc(x.text) + '</div></div>';
      }).join('');
      if (quiet && typing && m.querySelector('#sh-thread')) {
        var th0 = m.querySelector('#sh-thread'); th0.innerHTML = msgs || '<p style="color:#64748b">Mesaj yok.</p>'; th0.scrollTop = th0.scrollHeight; m.__sig = sig; return;
      }
      m.__sig = sig;
      m.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap"><div><b>' + esc(c.name) + '</b> · ' + esc(c.phone) + (c.brand ? ' · ' + esc(c.brand) : '') + ' <small id="sh-pres" style="margin-left:4px;color:' + (c.online ? '#16a34a' : '#94a3b8') + '">' + (c.online ? '● çevrimiçi' : '○ çevrimdışı') + '</small></div><div style="display:flex;gap:6px;flex-wrap:wrap">' + (shNarrow() ? '<button class="spx-b" id="sh-back" type="button">← Sohbetler</button>' : '') + '<button class="spx-b" id="sh-auto" type="button">Otomatik cevap gönder</button><button class="spx-b" id="sh-close" type="button">Sohbeti kapat</button><button class="spx-b" id="sh-del" type="button">Sohbeti sil</button></div></div>' +
        '<div id="sh-qr" style="display:none"></div>' +
        '<div id="sh-thread" style="flex:1;overflow:auto;max-height:55vh;display:flex;flex-direction:column;border:1px solid #e2e8f0;border-radius:10px;padding:8px">' + (msgs || '<p style="color:#64748b">Mesaj yok.</p>') + '</div>' +
        '<div id="sh-typing" style="min-height:16px;font-size:12px;color:#64748b;font-style:italic">' + (c.visitor_typing ? esc((c.name || '').trim().split(' ')[0]) + ' yazıyor…' : '') + '</div>' +
        '<div id="sh-sg" style="display:none;border:1px solid #e2e8f0;border-radius:10px;background:#fff;overflow:hidden"></div>' +
        '<div style="display:flex;gap:6px"><input id="sh-txt" placeholder="Yanıt yazın  ( / yazarak hazır mesaj seçin )" autocomplete="off" style="flex:1;border:1px solid #cbd5e1;border-radius:8px;padding:8px"><button class="spx-b p" id="sh-send" type="button">Gönder</button></div>';
      m.querySelector('#sh-txt').value = draft;
      var th = m.querySelector('#sh-thread'); if (th) th.scrollTop = th.scrollHeight;
      var fail = function (e) { alert(e && e.message ? e.message : 'İşlem yapılamadı'); };
      m.querySelector('#sh-send').onclick = function () { var inp = m.querySelector('#sh-txt'), t = inp.value.trim(); if (!t) return; inp.value = ''; call('POST', '/admin/chat/' + encodeURIComponent(cid) + '/reply', { text: t }).then(function () { loadChat(cid); loadChats(); }).catch(function (e) { inp.value = t; fail(e); }); };
      var sb = m.querySelector('#sh-back'); if (sb) sb.onclick = function () { CHAT_SEL = null; m.__sig = ''; shLayout(); loadChats(); };
      var sg = m.querySelector('#sh-sg'), sgItems = [];
      var sgHide = function () { sg.style.display = 'none'; sg.innerHTML = ''; sgItems = []; };
      var sgPick = function (q) { var inp = m.querySelector('#sh-txt'); inp.value = qrFill(q.text, c); sgHide(); inp.focus(); };
      var sgShow = function () {
        var inp = m.querySelector('#sh-txt'), v = inp.value;
        if (v.charAt(0) !== '/') { sgHide(); return; }
        if (!QR.items) { qrLoad(sgShow); return; }
        var term = v.slice(1).trim().toLocaleLowerCase('tr');
        sgItems = QR.items.filter(function (q) { return !term || (q.title + ' ' + q.text).toLocaleLowerCase('tr').indexOf(term) >= 0; }).slice(0, 5);
        if (!sgItems.length) { sgHide(); return; }
        sg.style.display = 'block';
        sg.innerHTML = sgItems.map(function (q, i) { return '<div data-sg="' + i + '" style="padding:8px 10px;cursor:pointer;border-bottom:1px solid #f1f5f9"><b style="font-size:13px">' + esc(q.title) + '</b><div style="font-size:12px;color:#64748b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + esc(qrFill(q.text, c)) + '</div></div>'; }).join('');
        Array.prototype.forEach.call(sg.querySelectorAll('[data-sg]'), function (d) { d.onclick = function () { sgPick(sgItems[parseInt(d.getAttribute('data-sg'), 10)]); }; });
      };
      m.querySelector('#sh-txt').oninput = function () {
        sgShow();
        var now = Date.now(); if (this.value && now - (m.__tt || 0) > 2500) { m.__tt = now; call('POST', '/admin/chat/' + encodeURIComponent(cid) + '/typing', {}).catch(function () { }); }
      };
      m.querySelector('#sh-txt').onkeydown = function (e) {
        if (e.key === 'Escape') { sgHide(); return; }
        if (e.key === 'Enter') { e.preventDefault(); if (sgItems.length) { sgPick(sgItems[0]); return; } m.querySelector('#sh-send').click(); }
      };
      m.querySelector('#sh-auto').onclick = function () { QR.open = !QR.open; QR.form = null; qrDraw(m, c, cid, fail); };
      m.querySelector('#sh-del').onclick = function () {
        if (!confirm('Bu sohbet panelden silinsin mi? (Mesaj kaydı sistemde saklanır; müşteri tekrar yazarsa sohbet yeniden görünür.)')) return;
        call('DELETE', '/admin/chat/' + encodeURIComponent(cid)).then(function () { CHAT_SEL = null; QR.open = false; m.__sig = ''; m.innerHTML = '<p style="color:#64748b">Soldan bir sohbet seçin.</p>'; shLayout(); loadChats(); }).catch(fail);
      };
      qrDraw(m, c, cid, fail);
      m.querySelector('#sh-close').onclick = function () { call('POST', '/admin/chat/' + encodeURIComponent(cid) + '/close', {}).then(function () { loadChat(cid); loadChats(); }).catch(fail); };
    }).catch(function () { });
  }
  function drawVade() {
    call('GET', '/tech-due').then(function (r) {
      var inp = 'border:1px solid #cbd5e1;border-radius:8px;padding:6px;font-size:13px;background:#fff';
      var h = grid([stat('Toplam usta borcu', TLf(r.total), ''), stat('Vadesi geçen', '<span style="color:' + (r.overdue_n ? '#dc2626' : '#15803d') + '">' + r.overdue_n + ' usta</span>', 'Bugün: ' + r.today)]) +
        '<div class="spx-card"><b>Usta bakiyeleri ve vade</b><small style="display:block;color:#64748b;margin:4px 0 8px">Her usta için "ne zamana kadar ödeyecek" tarihini girin. Vadesi geçenler en üstte kırmızı görünür; WhatsApp ile hatırlatma gönderebilirsiniz.</small>' +
        (r.items.length ? r.items.map(function (x) {
          var st = !x.due_date ? pill('vade yok', '#94a3b8') : x.overdue ? pill(Math.abs(x.days_left) + ' gün geçti', '#dc2626') : x.days_left === 0 ? pill('bugün', '#f59e0b') : pill(x.days_left + ' gün var', '#16a34a');
          var msg = 'Merhaba ' + (x.name || '').split(' ')[0] + ', ServisPlus hesabınızda ' + TLf(x.balance) + ' ödeme bakiyeniz görünüyor' + (x.due_date ? ' (vade: ' + x.due_date.split('-').reverse().join('.') + ')' : '') + '. Ödemeyi iletmenizi rica ederiz.';
          return '<div style="border:1px solid ' + (x.overdue ? '#fca5a5' : '#e2e8f0') + ';border-radius:12px;padding:12px;margin-top:10px;background:' + (x.overdue ? '#fef2f2' : '#fff') + '"><div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><b>' + esc(x.name) + '</b><b style="color:' + (x.balance > 0 ? '#dc2626' : '#15803d') + '">' + TLf(x.balance) + '</b></div>' +
            '<div style="display:flex;gap:8px;align-items:center;margin-top:8px;flex-wrap:wrap"><input type="date" data-vd="' + esc(x.technician_id) + '" value="' + esc(x.due_date) + '" style="' + inp + '">' + st + '</div>' +
            '<input data-vn="' + esc(x.technician_id) + '" value="' + esc(x.note) + '" placeholder="Not (örn. cuma ödeyecek)" style="' + inp + ';width:100%;margin-top:8px;box-sizing:border-box">' +
            '<div style="display:flex;gap:8px;margin-top:8px"><button class="spx-b p" data-vs="' + esc(x.technician_id) + '" style="flex:1">Kaydet</button>' + (x.phone && x.balance > 0 ? '<a class="spx-b" target="_blank" rel="noreferrer" href="' + waLink(x.phone, msg) + '" style="flex:1;text-align:center;text-decoration:none">💬 WhatsApp hatırlat</a>' : '') + '</div></div>';
        }).join('') : '<p style="color:#64748b">Borçlu usta yok.</p>') + '</div>';
      body().innerHTML = h;
      body().onclick = function (e) { var b = e.target.closest('[data-vs]'); if (!b) return; var id = b.getAttribute('data-vs'); call('PUT', '/tech-due/' + id, { due_date: body().querySelector('[data-vd="' + id + '"]').value, note: body().querySelector('[data-vn="' + id + '"]').value }).then(function () { toast('Kaydedildi'); drawVade(); }).catch(fail); };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }
  var HAR_D = '';
  function mapsMulti(addrs) { var a = addrs.filter(Boolean); if (!a.length) return ''; if (a.length === 1) return 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(a[0]); return 'https://www.google.com/maps/dir/?api=1&travelmode=driving&origin=' + encodeURIComponent(a[0]) + '&destination=' + encodeURIComponent(a[a.length - 1]) + (a.length > 2 ? '&waypoints=' + encodeURIComponent(a.slice(1, -1).join('|')) : ''); }
  function drawHarita() {
    call('GET', '/ops/day-map' + (HAR_D ? '?date=' + HAR_D : '')).then(function (r) {
      var adr = function (x) { return [x.customer_address, x.customer_district, x.customer_city].filter(Boolean).join(', '); };
      var by = {}; r.items.forEach(function (x) { var k = x.assigned_technician_name || 'Atanmamış'; (by[k] = by[k] || []).push(x); });
      var h = '<div class="spx-card"><b>Tarih</b> <input type="date" id="hr_d" value="' + esc(r.date) + '" style="margin-left:6px"> <b style="float:right">' + r.items.length + ' açık iş</b></div>';
      var names = Object.keys(by).sort(function (a, b) { return a === 'Atanmamış' ? -1 : b === 'Atanmamış' ? 1 : a.localeCompare(b, 'tr'); });
      if (!names.length) h += '<div class="spx-card" style="text-align:center;color:#64748b">Bu gün için açık iş yok.</div>';
      names.forEach(function (n) {
        var L = by[n], link = mapsMulti(L.map(adr));
        h += '<div class="spx-card"><div style="display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap"><b>' + (n === 'Atanmamış' ? '⚠ ' : '👤 ') + esc(n) + ' · ' + L.length + ' iş</b>' + (link ? '<a class="spx-b p" target="_blank" rel="noreferrer" href="' + link + '" style="text-decoration:none">🗺 Rotayı haritada aç</a>' : '') + '</div>' +
          L.map(function (x, i) { return '<div style="display:flex;gap:10px;padding:8px 0;border-top:1px solid #eef2f6"><b style="min-width:42px;color:#1d4ed8">' + esc((x.scheduled_at || '').slice(11, 16) || '—') + '</b><div style="flex:1"><div><b>' + esc(x.job_number) + '</b> · ' + esc(x.customer_name || '') + ' <small style="color:#64748b">' + esc([x.device_brand_name, x.device_type].filter(Boolean).join(' ')) + '</small></div><small style="color:#475569">' + esc(adr(x) || 'Adres yok') + '</small></div>' + (adr(x) ? '<a target="_blank" rel="noreferrer" href="' + mapsMulti([adr(x)]) + '" style="text-decoration:none;font-size:20px">📍</a>' : '') + '</div>'; }).join('') + '</div>';
      });
      body().innerHTML = h; $('#hr_d').onchange = function () { HAR_D = this.value; drawHarita(); };
    }).catch(function (e) { body().innerHTML = '<div class="spx-card">Yüklenemedi: ' + esc(e.message) + '</div>'; });
  }


  /* ===== Usta paneli: musteriye WhatsApp (gunun rotasi ve aylik karne zaten Daha Fazla sayfasinda) ===== */
  var TDAY = { d: null, t: 0, busy: false };
  function techDay() {
    var ex0 = document.getElementById('spx-route'); if (ex0) ex0.remove();
    /* iş detayı: müşteriye WhatsApp */
    var cc = document.querySelector('[data-testid="call-customer"]'), wb = document.getElementById('spx-wa');
    if (!cc || !document.body.classList.contains('spx-tech')) { if (wb) wb.remove(); return; }
    var digits = (cc.textContent || '').replace(/\D/g, '');
    if (digits.length >= 10 && !wb) {
      wb = document.createElement('a'); wb.id = 'spx-wa'; wb.target = '_blank'; wb.rel = 'noreferrer'; wb.className = 'notranslate';
      wb.href = waLink(digits, 'Merhaba, ServisPlus servis ekibinden yazıyorum. '); wb.textContent = '💬 WhatsApp';
      wb.style.cssText = 'display:inline-flex;align-items:center;gap:6px;margin:6px 0;background:#16a34a;color:#fff;border-radius:10px;padding:7px 12px;font-size:13px;font-weight:700;text-decoration:none';
      cc.parentElement.insertBefore(wb, cc.nextSibling);
    }
  }
  setInterval(techDay, 900);


  /* ===== Gorunum: yazi boyutu (admin Daha Fazlasi + usta Daha Fazla) ===== */
  (function () {
    var fs = parseInt(LS.get('spx_fs', '100'), 10); if (!(fs >= 85 && fs <= 130)) fs = 100;
    var st = document.createElement('style'); st.id = 'spx-fs'; document.head.appendChild(st);
    window.spxFont = function (v) { fs = Math.max(85, Math.min(130, v)); LS.set('spx_fs', String(fs)); st.textContent = fs === 100 ? '' : 'html{font-size:' + fs + '%!important}'; return fs; };
    window.spxFont(fs);
  })();
  function fontCard() {
    var cur = parseInt(LS.get('spx_fs', '100'), 10) || 100;
    return '<div class="spx-card" id="spx-fontcard" style="margin-top:16px"><b>Yazı boyutu</b><small style="display:block;color:#64748b;margin:2px 0 8px">Telefonda okumayı kolaylaştırır; bu cihazda saklanır.</small><div style="display:flex;gap:8px;align-items:center">' +
      '<button class="spx-b" data-fs="-8" style="flex:1;font-size:13px">A−</button><b id="spx-fsv" style="min-width:52px;text-align:center">%' + cur + '</b><button class="spx-b" data-fs="8" style="flex:1;font-size:18px">A+</button><button class="spx-b" data-fs="0" style="flex:1">Sıfırla</button></div></div>';
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-fs]'); if (!b || !window.spxFont) return;
    var d = parseInt(b.getAttribute('data-fs'), 10), cur = parseInt(LS.get('spx_fs', '100'), 10) || 100, v = window.spxFont(d === 0 ? 100 : cur + d), el = document.getElementById('spx-fsv'); if (el) el.textContent = '%' + v;
  });
  function techFontCard() {
    var ex = document.getElementById('spx-fontcard-t');
    if (!document.body.classList.contains('spx-tech') || location.pathname.replace(/\/$/, '') !== '/tech/more') { if (ex) ex.remove(); return; }
    if (ex) return; var m = document.querySelector('main'); if (!m) return;
    ex = document.createElement('div'); ex.id = 'spx-fontcard-t'; ex.className = 'notranslate'; ex.style.cssText = 'margin:12px 0;background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:14px'; ex.innerHTML = fontCard().replace(/^<div[^>]*>/, '').replace(/<\/div>$/, '');
    m.appendChild(ex);
  }
  setInterval(techFontCard, 1000);
  /* G160: panel yazi tipi site ile ayni (Source Sans 3) */
  (function(){ if (document.getElementById('spx-g160')) return; var st = document.createElement('style'); st.id = 'spx-g160';
    st.textContent = 'html body,html body *:not(code):not(pre):not(kbd):not(samp):not(.font-mono):not(svg):not(svg *){font-family:"Source Sans 3","Source Sans Pro",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif!important}html body{-webkit-font-smoothing:antialiased}'; document.head.appendChild(st); })();
  /* G165: usta isi tamamlayinca servis fisi PDF'i INMEZ; servis sayfasinda belge gorunur, ustte Yazdir / PDF Indir / Paylas. PDF'in kendisi degismedi. */
  (function () {
    var odisp = EventTarget.prototype.dispatchEvent, oclick = HTMLAnchorElement.prototype.click, RV = null;
    function isTech() { return document.body && (document.body.classList.contains('spx-tech') || /^\/tech/.test(location.pathname)); }
    function isReceipt(a, ev) {
      try { return a && a.tagName === 'A' && !a.__spxRaw && (!ev || ev.type === 'click') && /-servis-fisi\.pdf$/i.test(a.download || '') && /^blob:/.test(a.href || '') && isTech(); } catch (e) { return false; }
    }
    function intercept(a, redo) {
      var href = a.href, name = a.download;
      fetch(href).then(function (r) { return r.blob(); }).then(function (b) { rvShow(b, name); }).catch(function () { a.__spxRaw = true; redo(); });
    }
    EventTarget.prototype.dispatchEvent = function (ev) { var self = this, args = arguments; if (isReceipt(this, ev)) { intercept(this, function () { odisp.apply(self, args); }); return true; } return odisp.apply(this, arguments); };
    HTMLAnchorElement.prototype.click = function () { var self = this; if (isReceipt(this)) { intercept(this, function () { oclick.call(self); }); return; } return oclick.apply(this, arguments); };
    function rawSave(blob, name) { var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; a.__spxRaw = true; document.body.appendChild(a); oclick.call(a); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 4000); }
    function loadPdfJs() {
      return new Promise(function (res, rej) {
        if (window.pdfjsLib) return res(window.pdfjsLib);
        var s = document.createElement('script'); s.src = '/pdfjs/pdf.min.js?v=1';
        s.onload = function () { try { window.pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdfjs/pdf.worker.min.js?v=1'; res(window.pdfjsLib); } catch (e) { rej(e); } };
        s.onerror = function () { rej(new Error('pdfjs')); }; document.head.appendChild(s);
      });
    }
    function rvClose() { if (RV) { RV.remove(); RV = null; } }
    function rvPlace() {                                          /* usta panelinin ust cubugu ve alt menusu gorunur kalsin; belge ikisinin arasinda */
      if (!RV) return; var h = document.querySelector('header'), n = document.querySelector('nav.fixed'), fb = document.getElementById('spx-fbar'); if (fb && fb.offsetHeight > 0 && (!n || n.offsetHeight === 0 || n.offsetParent === null)) n = fb; var top = h ? Math.round(h.getBoundingClientRect().bottom) : 0, bot = n ? Math.round(window.innerHeight - n.getBoundingClientRect().top) : 0;
      RV.style.top = Math.max(0, top) + 'px'; RV.style.bottom = Math.max(0, bot) + 'px';
      [].forEach.call(RV.querySelectorAll('[data-a]'), function (b) { var z = 15; b.style.fontSize = z + 'px'; while (b.scrollWidth > b.clientWidth && z > 9) { z -= 0.5; b.style.fontSize = z + 'px'; } });
    }
    window.addEventListener('resize', rvPlace);
    function rvShow(blob, name) {
      rvClose();
      var dk = document.documentElement.classList.contains('spx-dark');
      var ov = RV = document.createElement('div'); ov.id = 'spx-rcv';
      ov.style.cssText = 'position:fixed;left:0;right:0;top:56px;bottom:66px;z-index:30;background:' + (dk ? '#0b1424' : '#e2e8f0') + ';display:flex;flex-direction:column;font-family:inherit';
      var bs = 'flex:1;min-width:0;height:44px;padding:0 4px;overflow:hidden;white-space:nowrap;border:0;border-radius:0;color:#fff;font:700 15px inherit;cursor:pointer;';
      ov.innerHTML = '<div style="display:flex;gap:6px;background:' + (dk ? '#111c33' : '#fff') + ';border-bottom:1px solid ' + (dk ? '#1e2d4a' : '#cbd5e1') + ';padding:8px">' +
        '<button data-a="x" style="' + bs + 'background:' + (dk ? '#1e2d4a' : '#e2e8f0') + ';color:' + (dk ? '#e2e8f0' : '#0f172a') + ';flex:.8">‹ Geri</button>' +
        '<button data-a="print" style="' + bs + 'background:#0a1f44">Yazdır</button><button data-a="dl" style="' + bs + 'background:#0a1f44">PDF İndir</button><button data-a="share" style="' + bs + 'background:#f27a1a">Paylaş</button></div>' +
        '<div data-pg style="flex:1;overflow:auto;padding:10px;-webkit-overflow-scrolling:touch"><div data-ld style="text-align:center;color:#64748b;padding:30px">Belge hazırlanıyor…</div></div>';
      document.body.appendChild(ov); rvPlace(); setTimeout(rvPlace, 300);
      var pg = ov.querySelector('[data-pg]'), cv = [];
      ov.onclick = function (e) {
        var b = e.target.closest('button[data-a]'); if (!b) return; var a = b.getAttribute('data-a');
        if (a === 'x') return rvClose();
        if (a === 'dl') return rawSave(blob, name);
        if (a === 'share') {
          var f; try { f = new File([blob], name, { type: 'application/pdf' }); } catch (er) { }
          if (f && navigator.canShare && navigator.canShare({ files: [f] })) { navigator.share({ files: [f], title: 'Servis belgesi' }).catch(function () { }); }
          else { rawSave(blob, name); toast('Paylaşım bu cihazda desteklenmiyor, PDF indirildi. Dosyayı mesajla gönderebilirsiniz.'); }
          return;
        }
        if (a === 'print') {
          var imgs = cv.map(function (c) { return '<img src="' + c.toDataURL('image/jpeg', 0.92) + '" style="width:100%;display:block;page-break-after:always">'; }).join('');
          if (!imgs) return rawSave(blob, name);
          var fr = document.createElement('iframe'); fr.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0'; document.body.appendChild(fr);
          var d = fr.contentWindow.document; d.open(); d.write('<!doctype html><html><head><meta charset="utf-8"><title>' + esc(name) + '</title><style>@page{margin:0}body{margin:0}</style></head><body>' + imgs + '</body></html>'); d.close();
          setTimeout(function () { try { fr.contentWindow.focus(); fr.contentWindow.print(); } catch (er) { rawSave(blob, name); } setTimeout(function () { fr.remove(); }, 60000); }, 400);
        }
      };
      blob.arrayBuffer().then(function (buf) { return loadPdfJs().then(function (lib) { return lib.getDocument({ data: new Uint8Array(buf) }).promise; }); }).then(function (doc) {
        pg.innerHTML = ''; var dpr = Math.min(2.5, window.devicePixelRatio || 1), chain = Promise.resolve();
        for (var i = 1; i <= doc.numPages; i++) (function (n) {
          chain = chain.then(function () { return doc.getPage(n); }).then(function (p) {
            var w = Math.min(pg.clientWidth - 20, 820), v1 = p.getViewport({ scale: 1 }), sc = (w * dpr) / v1.width, v = p.getViewport({ scale: sc });
            var c = document.createElement('canvas'); c.width = Math.round(v.width); c.height = Math.round(v.height); c.style.cssText = 'display:block;margin:0 auto 10px;background:#fff;border:1px solid #cbd5e1;width:' + w + 'px;max-width:100%;height:auto';
            pg.appendChild(c); cv.push(c); return p.render({ canvasContext: c.getContext('2d'), viewport: v }).promise;
          });
        })(i);
        return chain.then(function () {
          try { var c0 = cv[0], d = c0.getContext('2d').getImageData(0, 0, c0.width, c0.height).data, ink = 0; for (var q = 0; q < d.length; q += 400) { if (d[q] < 245 || d[q + 1] < 245 || d[q + 2] < 245) { ink++; if (ink > 5) break; } }
            if (ink <= 5) { var w = document.createElement('div'); w.style.cssText = 'background:#fef2f2;border:1px solid #fecaca;color:#991b1b;border-radius:10px;padding:10px;margin-bottom:8px;font-size:13px'; w.textContent = 'Belge boş çizildi (' + Math.round(blob.size / 1024) + ' KB, ' + doc.numPages + ' sayfa). Lütfen bu mesajın ekran görüntüsünü gönderin.'; pg.insertBefore(w, pg.firstChild); } } catch (e) { }
        });
      }).catch(function (er) {
        var u = URL.createObjectURL(blob), msg = (er && (er.message || er.name)) || 'bilinmiyor';
        pg.innerHTML = '<div style="background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:10px;padding:10px;margin-bottom:8px;font-size:13px">Önizleme çizilemedi (' + esc(String(msg).slice(0, 160)) + '). <b>PDF İndir</b> ile dosyayı indirip açabilirsiniz.<br>Belge boyutu: ' + Math.round(blob.size / 1024) + ' KB</div><iframe src="' + u + '" style="width:100%;height:70%;border:0;background:#fff"></iframe>';
      });
    }
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && RV) rvClose(); });
    window.__spxRv = rvShow;
  })();
  /* G163: React yan menuyu tamamen yeniden olusturdugunda (arka plan yenilemesi) bizim menu bos kalmasin: ayni mikro-gorevde hemen kur */
  (function(){ var busy = false; new MutationObserver(function(){ if (busy || !document.documentElement.classList.contains('spx-menu-on')) return;
    var ns = document.querySelectorAll('aside nav'), miss = false, i; for (i = 0; i < ns.length; i++) if (!ns[i].querySelector(':scope > [data-spx-own]')) { miss = true; break; }
    if (miss) { busy = true; try { tick(); tick(); menuAcc(); } catch (e) { } busy = false; }
    try { palSide(); } catch (e) { } }).observe(document.documentElement, { childList: true, subtree: true }); })();
  /* G164: grup basliklari "Genel Bakis" yazisi gibi (14px, normal kalinlik, Ilk Harfler Buyuk), siyah */
  (function(){ if (document.getElementById('spx-g164')) return; var st = document.createElement('style'); st.id = 'spx-g164';
    st.textContent = '[data-spx-own] .spx-gt svg{width:18px;height:18px;flex:none;margin-right:10px}[data-spx-own] .spx-gt .l{flex:1;min-width:0}html [data-spx-own] .spx-gt{text-transform:none!important;font-size:14px!important;font-weight:500!important;letter-spacing:0!important;color:#000!important}.spx-dark [data-spx-own] .spx-gt{color:#fff!important}'; document.head.appendChild(st); })();
  /* G159: React menuyu yeniden cizince eski (yerel) menu bir an gorunuyordu; CSS ile kalici gizle */
  (function(){ if (document.getElementById('spx-g159')) return; var st = document.createElement('style'); st.id = 'spx-g159';
    st.textContent = 'aside nav:has(> [data-spx-own]) > :not([data-spx-own]),html.spx-menu-on aside nav > :not([data-spx-own]){display:none!important}'; document.head.appendChild(st); })();

  /* ===== GUNCELLEME 153: silme yetkisi yalnizca Sahip; digerlerinde silme dugmeleri gizlenir (asil engel sunucuda) ===== */
  (function () { var st = document.createElement('style'); st.textContent =
    'body.spx-nodel [data-testid^="delete-"],body.spx-nodel [data-testid^="del-"],body.spx-nodel [data-testid="dealer-delete"],body.spx-nodel [data-testid="dealer-delete-tech"],body.spx-nodel [data-testid^="chat-delete-"],body.spx-nodel [data-testid="msg-delete"],body.spx-nodel [data-testid="gtab-trash"],body.spx-nodel #spx-bk,body.spx-nodel .spx-bkc,body.spx-nodel button:has(svg.lucide-trash-2),body.spx-nodel button:has(svg.lucide-trash),body.spx-nodel .spx-nodel-h{display:none!important}';
    document.head.appendChild(st); })();
  function noDelete() {
    var u = me(), on = u.role === 'admin' && (u.admin_role || 'owner') !== 'owner';
    document.body.classList.toggle('spx-nodel', on);
    if (!on) return;
    [].forEach.call(document.querySelectorAll('main button, main a[role=button], [role=dialog] button'), function (b) {
      if (b.classList.contains('spx-nodel-h')) return; var t = (b.textContent || '').trim();
      if (/^(Sil|Seçilenleri sil|Kalıcı olarak sil|Siliniyor…|Hepsini sil)$/i.test(t) || /^(Sil|Delete)$/i.test(b.getAttribute('aria-label') || '')) b.classList.add('spx-nodel-h');
    });
  }
  setInterval(noDelete, 700);

  /* ===== GUNCELLEME 151: arama kenar cubukta, toplu silme cubugu filtre yaninda, menu acilir-kapanir gruplar ===== */
  (function () { var st = document.createElement('style'); st.id = 'spx-g151'; st.textContent =
    '[data-spx-own] .spx-gt{cursor:pointer;display:flex;justify-content:space-between;align-items:center;user-select:none;padding:7px 12px;margin:2px 0 0;border-radius:6px}[data-spx-own] .spx-gt:hover{background:#f1f5f9;color:#0f172a}' +
    '[data-spx-own] .spx-gt::after{content:"";width:6px;height:6px;border-right:2px solid #94a3b8;border-bottom:2px solid #94a3b8;transform:rotate(45deg);margin-right:3px;transition:transform .15s}[data-spx-own] .spx-gt.c::after{transform:rotate(-45deg)}' +
    '[data-spx-own] .spx-gt{color:#000!important;font-size:14px!important;font-weight:800!important;letter-spacing:.05em!important;background:#eef1f5;border-left:4px solid #0a1f44;border-radius:0!important;padding:10px 12px!important;margin:8px 0 2px!important}[data-spx-own] .spx-gt:hover{background:#e2e8f0!important}.spx-dark [data-spx-own] .spx-gt{color:#fff!important;background:#1d2a42;border-left-color:#93c5fd}' +
    '.spx-dark [data-spx-own] .spx-gt:hover{background:#1d2a42;color:#fff}' +
    '@media(min-width:1024px){body:not(.spx-tech) div:has(>aside.w-64){position:sticky;top:0;height:100vh;align-self:flex-start;flex-shrink:0}body:not(.spx-tech) aside.w-64{height:100vh}body:not(.spx-tech) aside.w-64>nav{min-height:0;overscroll-behavior:contain;scrollbar-width:thin}}' +
    '.spx-sbs{padding:10px 12px 2px}.spx-sbs button{width:100%;display:flex;align-items:center;gap:8px;height:36px;padding:0 10px;border:1px solid #e2e8f0;border-radius:6px;background:#f8fafc;color:#64748b;font-size:13px;cursor:pointer;text-align:left}'+'.spx-sbs button:hover{background:#fff;border-color:#cbd5e1}' +
    '.spx-sbs kbd{margin-left:auto;font:11px inherit;border:1px solid #cbd5e1;border-radius:4px;padding:0 5px;color:#94a3b8;background:#fff}.spx-dark .spx-sbs button{background:#111c33;border-color:#1e2d4a;color:#94a3b8}';
    document.head.appendChild(st); })();
  function palSide() {
    var on = /^\/admin/.test(location.pathname) && !document.body.classList.contains('spx-tech') && !!LS.get('token', '') && !/^\/admin\/login/.test(location.pathname);
    [].forEach.call(document.querySelectorAll('aside'), function (as) {          /* masaustu menusu + telefon cekmecesi */
      var ex = as.querySelector(':scope > .spx-sbs'), hd = as.firstElementChild;
      if (!on) { if (ex) ex.remove(); return; }
      if (ex || !hd) return;
      var d = document.createElement('div'); d.className = 'spx-sbs notranslate';
      d.innerHTML = '<button type="button" aria-label="Panelde ara">🔍 <span>Ara…</span><kbd>Ctrl K</kbd></button>';
      d.firstChild.onclick = function () { closeMobile(); palOpen(); };
      hd.insertAdjacentElement('afterend', d);
    });
  }
  setInterval(palSide, 700);
  function bkPlace() {
    var b = document.getElementById('spx-bk'); if (!b) return;
    var jf = document.getElementById('spx-jf'), tgt = null, mode = 'after';
    if (jf && /^\/admin\/jobs\/?$/.test(location.pathname)) tgt = jf;
    else { var h = document.querySelector('main h1'); if (h) { tgt = h.parentElement && h.parentElement.parentElement && h.parentElement.parentElement.tagName !== 'MAIN' ? h.parentElement.parentElement : h.parentElement; } }
    if (!tgt || !tgt.parentNode) return;
    if (b.previousElementSibling !== tgt) tgt.insertAdjacentElement('afterend', b);
  }
  setInterval(bkPlace, 500);
  var MG = { set: null, path: '' };
  function mgSave() { try { LS.set('spx_mg', JSON.stringify(Object.keys(MG.set || {}))); } catch (e) { } }
  function menuAccOne(own, changed) {
    var kids = own.children, cur = '', i, k, act = null;
    if (!MG.set) { MG.set = {}; try { (JSON.parse(LS.get('spx_mg', '[]')) || []).forEach(function (n) { MG.set[n] = 1; }); } catch (e) { } }
    if (changed) {                                                /* sayfa degisince yalnizca AKTIF grubu ac; hicbir grubu kendiliginden kapatma */
      for (i = 0; i < kids.length; i++) { k = kids[i]; if (k.classList.contains('spx-gt')) cur = k.getAttribute('data-g') || k.textContent; else if (k.querySelector('a.spx-it.on')) { act = cur; break; } }
      if (act !== null) MG._seen = true;
      if (act && !MG.set[act]) { MG.set[act] = 1; mgSave(); }
    }
    cur = null; var gh = null, gsum = 0, gbang = false, gtl = [];
    for (i = 0; i < kids.length; i++) {
      k = kids[i];
      if (k.classList.contains('spx-gt')) { if (!k.getAttribute('data-g')) k.setAttribute('data-g', k.textContent); cur = k.getAttribute('data-g'); k.classList.toggle('c', !MG.set[cur]); gh = k; gsum = 0; gbang = false; gtl.push(k); }
      else if (cur !== null) {
        var d = MG.set[cur] ? '' : 'none'; if (k.style.display !== d) k.style.display = d;
        [].forEach.call(k.querySelectorAll('.spx-bd:not(.spx-od)'), function (b) { var t = (b.textContent || '').trim(); if (t === '!') gbang = true; else gsum += parseInt(t, 10) || 0; gh._s = gsum; gh._b = gbang; });
      }
    }
    gtl.forEach(function (g) {                                   /* kapali grubun basligina icindeki bildirimlerin toplami */
      var show = g.classList.contains('c') && (g._s > 0 || g._b), t = g._b && !g._s ? '!' : String(g._s || ''), e = g.querySelector('.spx-gb');
      if (!show) { if (e) e.remove(); return; }
      if (!e) { e = document.createElement('span'); e.className = 'spx-bd spx-gb'; e.style.cssText = 'margin-left:auto;margin-right:8px'; g.insertBefore(e, null); }
      if (e.textContent !== t) e.textContent = t;
    });
  }
  function menuAcc() {                                            /* masaustu menusu ve telefon cekmecesi ayri kopyalar: hepsini isle */
    var owns = document.querySelectorAll('[data-spx-own]'); if (!owns.length) return;
    var p = location.pathname + location.search, changed = MG.path !== p; MG._seen = false;
    [].forEach.call(owns, function (o) { if (o.querySelector('.spx-gt')) menuAccOne(o, changed); });
    if (changed && (MG._seen || !MG.path)) MG.path = p;
  }
  setInterval(menuAcc, 150);
  document.addEventListener('click', function (e) {
    var g = e.target.closest && e.target.closest('[data-spx-own] .spx-gt'); if (!g) return;
    var n = g.getAttribute('data-g') || g.textContent, nav = g.closest('nav'), top = g.getBoundingClientRect().top;
    if (!MG.set) MG.set = {}; if (MG.set[n]) delete MG.set[n]; else MG.set[n] = 1; mgSave(); menuAcc();
    if (nav) nav.scrollTop += g.getBoundingClientRect().top - top;           /* tiklanan baslik ekranda ayni yerde kalsin */
  });

  /* ===== GUNCELLEME 150: aylik muhasebe + usta hakedis raporu, KVKK araci, mesaj sablonlari, cevrimdisi okuma ===== */
  function tl(n) { return Number(n || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ₺'; }
  function dl(name, text, mime) { var b = new Blob(['﻿' + text], { type: mime || 'text/csv;charset=utf-8' }), a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = name; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500); }
  function csvRow(a) { return a.map(function (v) { v = String(v == null ? '' : v); return /[";\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }).join(';'); }
  var RPT = { busy: false };
  var MON = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
  var CARD = 'background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:12px 16px;margin-bottom:16px;';
  var TH = 'text-align:right;padding:6px 8px;border-bottom:1px solid #e2e8f0;font-size:12.5px;white-space:nowrap', TD = 'text-align:right;padding:6px 8px;border-bottom:1px solid #f1f5f9;font-size:13px;white-space:nowrap';
  function payRange(k) {
    var n = new Date(), y = n.getFullYear(), m = n.getMonth(), p = function (x) { return (x < 10 ? '0' : '') + x; }, last = function (yy, mm) { return new Date(yy, mm + 1, 0).getDate(); };
    if (k === 'this') return '?date_from=' + y + '-' + p(m + 1) + '-01&date_to=' + y + '-' + p(m + 1) + '-' + p(last(y, m));
    if (k === 'prev') { var yy = m ? y : y - 1, mm = m ? m - 1 : 11; return '?date_from=' + yy + '-' + p(mm + 1) + '-01&date_to=' + yy + '-' + p(mm + 1) + '-' + p(last(yy, mm)); }
    if (k === 'year') return '?date_from=' + y + '-01-01&date_to=' + y + '-12-31';
    return '';
  }
  function rptLoad(card) {
    var yr = +card.querySelector('#spx-rp-y').value, rk = card.querySelector('#spx-rp-r').value, box = card.querySelector('#spx-rp-b');
    box.innerHTML = '<div style="color:#64748b;padding:8px">Yükleniyor…</div>';
    Promise.all([call('GET', '/reports/monthly?year=' + yr), call('GET', '/reports/tech-payouts' + payRange(rk))]).then(function (z) {
      var m = z[0], p = z[1], h = '<div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%;min-width:560px"><tr><th style="' + TH + ';text-align:left">Ay</th><th style="' + TH + '">Gelir</th><th style="' + TH + '">Gider</th><th style="' + TH + '">Usta payı</th><th style="' + TH + '">Net</th></tr>';
      m.months.forEach(function (r, i) { if (!(r.income || r.expense || r.tech_prim)) return; h += '<tr><td style="' + TD + ';text-align:left">' + MON[i] + '</td><td style="' + TD + '">' + tl(r.income) + '</td><td style="' + TD + '">' + tl(r.expense) + '</td><td style="' + TD + '">' + tl(r.tech_prim) + '</td><td style="' + TD + ';font-weight:700;color:' + (r.net < 0 ? '#b91c1c' : '#15803d') + '">' + tl(r.net) + '</td></tr>'; });
      h += '<tr style="background:#f8fafc;font-weight:800"><td style="' + TD + ';text-align:left">' + yr + ' toplam</td><td style="' + TD + '">' + tl(m.total.income) + '</td><td style="' + TD + '">' + tl(m.total.expense) + '</td><td style="' + TD + '">' + tl(m.total.tech_prim) + '</td><td style="' + TD + '">' + tl(m.total.net) + '</td></tr></table></div>';
      h += '<div style="font-size:12px;color:#64748b;margin:6px 0 14px">Net = gelir − gider − usta payı (kasada kalan). Veri, kasa hareketlerinden gelir; tamamlanmamış işler dahil değildir.</div>';
      if (m.expense_categories.length) h += '<div style="font-size:13px;margin-bottom:14px"><b>Gider dağılımı:</b> ' + m.expense_categories.map(function (c) { return esc(c.category) + ' <b>' + tl(c.amount) + '</b>'; }).join(' · ') + '</div>';
      h += '<div style="font-weight:800;margin:6px 0">Usta hakediş özeti</div>';
      if (!p.rows.length) h += '<div style="color:#64748b;font-size:13px">Seçilen dönemde usta hareketi yok.</div>';
      else { h += '<div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%;min-width:620px"><tr><th style="' + TH + ';text-align:left">Usta</th><th style="' + TH + '">İş</th><th style="' + TH + '">Ciro</th><th style="' + TH + '">Usta payı</th><th style="' + TH + '">Şirkete borç</th><th style="' + TH + '">Ödenen</th><th style="' + TH + '">Kalan borç</th></tr>';
        p.rows.forEach(function (r) { h += '<tr><td style="' + TD + ';text-align:left">' + esc(r.name) + '</td><td style="' + TD + '">' + r.jobs + '</td><td style="' + TD + '">' + tl(r.revenue) + '</td><td style="' + TD + '">' + tl(r.prim) + '</td><td style="' + TD + '">' + tl(r.debt) + '</td><td style="' + TD + '">' + tl(r.paid) + '</td><td style="' + TD + ';font-weight:700;color:' + (r.balance > 0 ? '#b45309' : '#15803d') + '">' + tl(r.balance) + '</td></tr>'; });
        h += '<tr style="background:#f8fafc;font-weight:800"><td style="' + TD + ';text-align:left">Toplam</td><td style="' + TD + '">' + p.total.jobs + '</td><td style="' + TD + '">' + tl(p.total.revenue) + '</td><td style="' + TD + '">' + tl(p.total.prim) + '</td><td style="' + TD + '">' + tl(p.total.debt) + '</td><td style="' + TD + '">' + tl(p.total.paid) + '</td><td style="' + TD + '">' + tl(p.total.balance) + '</td></tr></table></div>'; }
      h += '<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap"><button type="button" id="spx-rp-c1" style="border:1px solid #cbd5e1;background:#fff;border-radius:8px;padding:8px 12px;font-weight:700;cursor:pointer">⬇ Aylık raporu CSV</button><button type="button" id="spx-rp-c2" style="border:1px solid #cbd5e1;background:#fff;border-radius:8px;padding:8px 12px;font-weight:700;cursor:pointer">⬇ Hakediş CSV</button></div>';
      box.innerHTML = h;
      box.querySelector('#spx-rp-c1').onclick = function () { dl('aylik-rapor-' + yr + '.csv', [csvRow(['Ay', 'Gelir', 'Gider', 'Usta payı', 'Şirkete borç', 'Net'])].concat(m.months.map(function (r, i) { return csvRow([MON[i], r.income, r.expense, r.tech_prim, r.tech_debt, r.net]); })).join('\r\n')); };
      box.querySelector('#spx-rp-c2').onclick = function () { dl('usta-hakedis.csv', [csvRow(['Usta', 'İş', 'Ciro', 'Usta payı', 'Şirkete borç', 'Ödenen', 'Kalan borç'])].concat(p.rows.map(function (r) { return csvRow([r.name, r.jobs, r.revenue, r.prim, r.debt, r.paid, r.balance]); })).join('\r\n')); };
    }).catch(function (e) { box.innerHTML = '<div style="color:#b91c1c;padding:8px">' + esc(e.message || 'Rapor alınamadı') + '</div>'; });
  }
  function reportsCard() {
    var ex = document.getElementById('spx-rp'), on = /^\/admin\/(reports|accounting)\/?$/.test(location.pathname) && !document.body.classList.contains('spx-tech'), mn = document.querySelector('main');
    if (!on || !mn) { if (ex) ex.remove(); return; }
    if (ex) return;
    var y = new Date().getFullYear(), d = document.createElement('details'); d.id = 'spx-rp'; d.style.cssText = CARD;
    d.innerHTML = '<summary style="cursor:pointer;font-weight:800;color:#0a1f44">📊 Aylık gelir/gider ve usta hakediş raporu</summary><div style="display:flex;gap:10px;flex-wrap:wrap;margin:12px 0"><select id="spx-rp-y" style="border:1px solid #cbd5e1;border-radius:8px;padding:7px 10px"><option>' + y + '</option><option>' + (y - 1) + '</option><option>' + (y - 2) + '</option></select><select id="spx-rp-r" style="border:1px solid #cbd5e1;border-radius:8px;padding:7px 10px"><option value="this">Hakediş: bu ay</option><option value="prev">Hakediş: geçen ay</option><option value="year">Hakediş: bu yıl</option><option value="all">Hakediş: tüm zamanlar</option></select></div><div id="spx-rp-b"></div>';
    mn.insertAdjacentElement('afterbegin', d);
    d.addEventListener('toggle', function () { if (d.open) rptLoad(d); });
    d.querySelector('#spx-rp-y').onchange = d.querySelector('#spx-rp-r').onchange = function () { rptLoad(d); };
  }
  setInterval(reportsCard, 900);

  /* --- KVKK veri talebi araci (Guvenlik sayfasi) --- */
  function kvkkCard() {
    var ex = document.getElementById('spx-kv'), on = /^\/admin\/security\/?$/.test(location.pathname) && !document.body.classList.contains('spx-tech'), mn = document.querySelector('main');
    if (!on || !mn) { if (ex) ex.remove(); return; }
    if (ex) return;
    var d = document.createElement('details'); d.id = 'spx-kv'; d.style.cssText = CARD;
    d.innerHTML = '<summary style="cursor:pointer;font-weight:800;color:#0a1f44">🔐 KVKK veri talebi aracı (müşteri verisini indir / sil)</summary><div style="font-size:12.5px;color:#64748b;margin:10px 0">Ad, telefon veya e-posta ile müşteriyi bulun. <b>İndir</b> müşterinin tüm kayıtlarını JSON verir. <b>Sil</b> kişisel veriyi anonimleştirir (servis kayıtlarındaki ad/telefon/adres, cihazlar, mesajlar, hesap silinir); kasa hareketleri yasal saklama için kalır ama kişiyle bağı kopar. <b>Geri alınamaz.</b> Her işlem kayda geçer.</div><div style="display:flex;gap:8px;flex-wrap:wrap"><input id="spx-kv-q" placeholder="En az 3 karakter" style="flex:1;min-width:200px;border:1px solid #cbd5e1;border-radius:8px;padding:9px 11px"><button type="button" id="spx-kv-go" style="background:#0a1f44;color:#fff;border:0;border-radius:8px;padding:9px 16px;font-weight:700;cursor:pointer">Ara</button></div><div id="spx-kv-r" style="margin-top:10px"></div>';
    mn.insertAdjacentElement('afterbegin', d);
    var q = d.querySelector('#spx-kv-q'), r = d.querySelector('#spx-kv-r');
    function go() {
      r.innerHTML = 'Aranıyor…';
      call('GET', '/security/kvkk/search?q=' + encodeURIComponent(q.value)).then(function (x) {
        if (!x.results.length) { r.innerHTML = '<div style="color:#64748b">Sonuç yok.</div>'; return; }
        r.innerHTML = x.results.map(function (c) { return '<div data-id="' + esc(c.id) + '" style="border:1px solid #e2e8f0;border-radius:10px;padding:10px;margin-bottom:8px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;justify-content:space-between"><div><b>' + esc(c.name) + '</b> · ' + esc(c.phone) + (c.email ? ' · ' + esc(c.email) : '') + '<div style="font-size:12px;color:#64748b">' + c.jobs + ' servis kaydı · ' + c.devices + ' cihaz</div></div><div style="display:flex;gap:6px"><button type="button" data-a="x" style="border:1px solid #cbd5e1;background:#fff;border-radius:8px;padding:7px 11px;font-weight:700;cursor:pointer">⬇ İndir</button><button type="button" data-a="d" style="border:1px solid #fecaca;background:#fef2f2;color:#b91c1c;border-radius:8px;padding:7px 11px;font-weight:700;cursor:pointer">🗑 Sil</button></div></div>'; }).join('');
      }).catch(function (e) { r.innerHTML = '<div style="color:#b91c1c">' + esc(e.message) + '</div>'; });
    }
    d.querySelector('#spx-kv-go').onclick = go; q.onkeydown = function (e) { if (e.key === 'Enter') go(); };
    r.onclick = function (e) {
      var b = e.target.closest('button[data-a]'); if (!b) return; var id = b.closest('[data-id]').getAttribute('data-id');
      if (b.getAttribute('data-a') === 'x') call('GET', '/security/kvkk/export/' + id).then(function (j) { dl('kvkk-' + id.slice(0, 8) + '.json', JSON.stringify(j, null, 2), 'application/json'); toast('Veri indirildi'); }).catch(fail);
      else { var t = window.prompt('Bu müşterinin kişisel verisi kalıcı olarak silinecek/anonimleştirilecek.\nOnaylamak için SİL yazın:'); if (t == null) return; call('POST', '/security/kvkk/erase/' + id, { confirm: t }).then(function (x) { toast('Silindi: ' + x.jobs_anonymized + ' kayıt anonimleştirildi'); go(); }).catch(fail); }
    };
  }
  setInterval(kvkkCard, 900);

  /* ===== G168: Sistem Sagligi > Surumler ve geri alma (yalniz sahip) ===== */
  function surumCard() {
    var ex = document.getElementById('spx-sv'), u = me(), on = /^\/admin\/governance\/?$/.test(location.pathname) && !document.body.classList.contains('spx-tech') && (!u.admin_role || u.admin_role === 'owner'), mn = document.querySelector('main');
    if (!on || !mn) { if (ex) ex.remove(); return; }
    if (ex) return;
    var d = document.createElement('details'); d.id = 'spx-sv'; d.style.cssText = CARD; d.open = true;
    d.innerHTML = '<summary style="cursor:pointer;font-weight:800;color:#0a1f44">🛟 Sürümler ve geri alma</summary><div data-b style="margin-top:10px;font-size:13px;color:#334155">Yükleniyor…</div>';
    mn.insertAdjacentElement('afterbegin', d);
    var b = d.querySelector('[data-b]');
    function load() {
      call('GET', '/governance/surumler').then(function (x) {
        var h = '<div style="margin-bottom:8px">Yayındaki son sürüm: <b>' + esc(x.son_sha || '—') + '</b> · Güncellemeler: ' + (x.sabit ? '<b style="color:#b91c1c">DURDURULDU</b> (' + esc(x.sabit) + ')' : '<b style="color:#166534">açık</b>') + '</div>';
        if (x.bekleyen_istek) h += '<div style="background:#fef3c7;border:1px solid #fcd34d;padding:8px 10px;margin-bottom:8px">Geri alma isteği sırada (<b>' + esc(x.bekleyen_istek) + '</b>). Sunucu en geç 5 dakikada uygular.</div>';
        if (x.sabit) h += '<button class="spx-b" data-un style="margin-bottom:10px">Güncellemeleri sürdür</button> <span style="color:#64748b">(GitHub\'daki son sürüm yayına alınır)</span>';
        if (!x.kurulu || !x.surumler.length) h += '<div style="color:#64748b;margin:6px 0">Henüz kayıtlı sürüm yok. Bir sonraki yayından itibaren her yayından önce yedek alınır.</div>';
        else h += '<div style="color:#64748b;margin-bottom:6px">Her yayından önce canlı dosyaların yedeği alınır (son 6). Seçtiğiniz yedek, o yayından ÖNCEKİ hâle döner.</div>' + x.surumler.map(function (v) { return '<div style="display:flex;gap:8px;align-items:center;justify-content:space-between;border:1px solid #e2e8f0;padding:8px 10px;margin-bottom:6px"><span>' + esc(v.tarih) + ' · önceki: <b>' + esc(v.onceki_sha) + '</b> · ' + v.boyut_kb + ' KB</span><button class="spx-b d" data-id="' + esc(v.id) + '">Bu sürüme dön</button></div>'; }).join('');
        h += '<div style="color:#64748b;margin:8px 0;font-size:12.5px">Panel hiç açılmazsa: cPanel > File Manager > ana klasörde boş bir <b>geri-al.txt</b> dosyası oluşturun; 5 dakika içinde önceki sürüme dönülür. Telefona kesinti bildirimi için sunucuda <b>NTFY_KONU</b> ayarı gerekir.</div>';
        if (x.log && x.log.length) h += '<details><summary style="cursor:pointer;color:#64748b">Son yayın kayıtları</summary><pre style="white-space:pre-wrap;font-size:11.5px;background:#f8fafc;border:1px solid #e2e8f0;padding:8px;margin-top:6px">' + esc(x.log.join('\n')) + '</pre></details>';
        b.innerHTML = h;
        var un = b.querySelector('[data-un]'); if (un) un.onclick = function () { call('POST', '/governance/surumler/sabit-kaldir').then(function (r) { toast(r.mesaj); load(); }).catch(function (e) { toast(e.message); }); };
        [].forEach.call(b.querySelectorAll('[data-id]'), function (btn) { btn.onclick = function () {
          var c = window.prompt('Bu sürüme dönülecek ve güncellemeler durdurulacak.\nOnaylamak için GERİ AL yazın:'); if (!c) return;
          call('POST', '/governance/surumler/geri-al', { id: btn.getAttribute('data-id'), confirm: c }).then(function (r) { toast(r.mesaj); load(); }).catch(function (e) { toast(e.message); });
        }; });
      }).catch(function (e) { b.innerHTML = '<span style="color:#b91c1c">' + esc(e.message) + '</span>'; });
    }
    load();
  }
  setInterval(surumCard, 900);

  /* ===== Yedekler: simdi yedek al + eski yedekleri sil (yalniz sahip) ===== */
  function yedekCard() {
    var ex = document.getElementById('spx-yd'), u = me(), on = /^\/admin\/governance\/?$/.test(location.pathname) && !document.body.classList.contains('spx-tech') && (!u.admin_role || u.admin_role === 'owner'), mn = document.querySelector('main');
    if (!on || !mn) { if (ex) ex.remove(); return; }
    if (ex) return;
    var d = document.createElement('details'); d.id = 'spx-yd'; d.style.cssText = CARD; d.open = true;
    d.innerHTML = '<summary style="cursor:pointer;font-weight:800;color:#0a1f44">💾 Yedekler — şimdi al / eskileri sil</summary><div data-b style="margin-top:10px;font-size:13px;color:#334155">Yükleniyor…</div>';
    mn.insertAdjacentElement('afterbegin', d);
    var b = d.querySelector('[data-b]'), busy = false;
    function mb(n) { return (n / 1048576).toFixed(n > 1048576 * 10 ? 0 : 1) + ' MB'; }
    function kindTr(k) { return k === 'manual' ? 'Elle' : k === 'auto' ? 'Otomatik' : k === 'pre-restore' || k === 'restore' ? 'Geri yüklemeden önce' : k; }
    function load() {
      call('GET', '/governance/backups').then(function (x) {
        var it = x.items || [], tot = it.reduce(function (a, v) { return a + v.size; }, 0);
        var h = '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px"><button class="spx-b" data-now' + (busy ? ' disabled' : '') + '>' + (busy ? 'Yedek alınıyor…' : '＋ Şimdi yedek al') + '</button>' +
          '<span style="color:#64748b">' + it.length + ' yedek · toplam ' + mb(tot) + ' · otomatik yedekte son <b>' + esc((x.settings || {}).keep) + '</b> adet tutulur</span></div>';
        if (!it.length) h += '<div style="color:#b91c1c;margin:6px 0">Hiç yedek yok. “Şimdi yedek al”a basın.</div>';
        else {
          h += '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px"><label><input type="checkbox" data-all> Tümünü seç</label><button class="spx-b d" data-delsel>Seçilenleri sil</button><button class="spx-b d" data-keep>Son N hariç hepsini sil…</button></div>';
          h += it.map(function (v, i) {
            return '<div style="display:flex;gap:8px;align-items:center;border:1px solid #e2e8f0;padding:7px 10px;margin-bottom:5px;flex-wrap:wrap"><input type="checkbox" data-n="' + esc(v.name) + '"><span style="flex:1;min-width:200px"><b>' + esc(new Date(v.at).toLocaleString('tr-TR')) + '</b> · ' + esc(kindTr(v.kind)) + ' · ' + mb(v.size) + (i === 0 ? ' <span style="color:#166534">(en yeni)</span>' : '') + '<br><span style="color:#94a3b8;font-size:11.5px">' + esc(v.name) + '</span></span><button class="spx-b" data-vf="' + esc(v.name) + '">Doğrula</button><button class="spx-b d" data-del="' + esc(v.name) + '">Sil</button></div>';
          }).join('');
        }
        b.innerHTML = h;
        function del(names, msg) {
          if (!names.length) { toast('Önce yedek seçin'); return; }
          var all = names.length >= it.length;
          if (!window.confirm(msg + (all ? '\n\nDİKKAT: Hiç yedek kalmayacak!' : ''))) return;
          names.reduce(function (p, n) { return p.then(function () { return call('DELETE', '/governance/backups/' + encodeURIComponent(n)); }); }, Promise.resolve())
            .then(function () { toast(names.length + ' yedek silindi'); load(); }).catch(function (e) { fail(e); load(); });
        }
        b.querySelector('[data-now]').onclick = function () {
          if (busy) return; busy = true; load();
          call('POST', '/governance/backups').then(function (r) { busy = false; toast('Yedek alındı ✔ ' + (r.size ? mb(r.size) : '')); load(); }).catch(function (e) { busy = false; fail(e); load(); });
        };
        var all = b.querySelector('[data-all]');
        if (all) {
          all.onchange = function () { [].forEach.call(b.querySelectorAll('[data-n]'), function (c) { c.checked = all.checked; }); };
          b.querySelector('[data-delsel]').onclick = function () { var n = [].filter.call(b.querySelectorAll('[data-n]'), function (c) { return c.checked; }).map(function (c) { return c.getAttribute('data-n'); }); del(n, n.length + ' yedek kalıcı olarak silinecek. Emin misiniz?'); };
          b.querySelector('[data-keep]').onclick = function () {
            var k = window.prompt('En yeni kaç yedek kalsın? (1 veya daha fazla)', '3'); if (k === null) return; k = parseInt(k, 10);
            if (!(k >= 1)) { toast('Geçerli bir sayı girin'); return; }
            del(it.slice(k).map(function (v) { return v.name; }), 'En yeni ' + k + ' yedek kalacak, ' + Math.max(0, it.length - k) + ' eski yedek silinecek. Emin misiniz?');
          };
          [].forEach.call(b.querySelectorAll('[data-del]'), function (btn) { btn.onclick = function () { del([btn.getAttribute('data-del')], 'Bu yedek silinecek:\n' + btn.getAttribute('data-del')); }; });
          [].forEach.call(b.querySelectorAll('[data-vf]'), function (btn) { btn.onclick = function () { btn.textContent = '…'; call('POST', '/governance/backups/' + encodeURIComponent(btn.getAttribute('data-vf')) + '/verify').then(function (r) { btn.textContent = (r.ok === false || r.valid === false) ? 'BOZUK ✖' : 'Sağlam ✔'; }).catch(function (e) { btn.textContent = 'Doğrula'; fail(e); }); }; });
        }
      }).catch(function (e) { b.innerHTML = '<span style="color:#b91c1c">' + esc(e.message) + '</span>'; });
    }
    load();
  }
  setInterval(yedekCard, 900);

  /* --- Is detayi: musteriye sablonlu mesaj (WhatsApp / SMS) + sablon duzenleme --- */
  function tplModal(jid) {
    var old = document.getElementById('spx-tpm'); if (old) old.remove();
    Promise.all([call('GET', '/msg-templates')]).then(function (z) {
      var T = z[0].templates, cur = 0, phone = '', m = document.createElement('div'); m.id = 'spx-tpm'; m.className = 'notranslate';
      m.style.cssText = 'position:fixed;inset:0;z-index:100002;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:14px';
      var bt = 'border-radius:8px;padding:10px 13px;font-size:14px;font-weight:700;cursor:pointer;';
      function chips() { return T.map(function (x, i) { var on = i === cur; return '<button type="button" data-i="' + i + '" style="border:1px solid ' + (on ? '#2563eb' : '#e2e8f0') + ';background:' + (on ? '#2563eb' : '#fff') + ';color:' + (on ? '#fff' : '#0f172a') + ';border-radius:8px;padding:7px 11px;font-size:12px;font-weight:700;cursor:pointer">' + esc(x.name) + '</button>'; }).join(''); }
      function fill() { call('POST', '/msg-templates/render', { job_id: jid, template_id: T[cur].id }).then(function (r) { phone = r.phone; m.querySelector('#tp_t').value = r.text; m.querySelector('#tp_c').innerHTML = chips(); }).catch(fail); }
      function view() {
        m.innerHTML = '<div style="width:100%;max-width:420px;max-height:92vh;overflow:auto;background:#fff;color:#0f172a;border-radius:14px;padding:20px;box-shadow:0 20px 60px rgba(0,0,0,.35);font-family:system-ui,sans-serif;position:relative"><button id="tp_x" style="position:absolute;right:14px;top:12px;border:0;background:none;font-size:18px;cursor:pointer">✕</button><div style="font-size:17px;font-weight:800;margin-bottom:10px">✉ Müşteriye mesaj</div><div id="tp_c" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">' + chips() + '</div><textarea id="tp_t" rows="7" style="width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:10px;font-size:14px;line-height:1.45"></textarea><div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap"><button id="tp_wa" style="' + bt + 'flex:1;background:#059669;color:#fff;border:0">💬 WhatsApp</button><button id="tp_sms" style="' + bt + 'flex:1;background:#0a1f44;color:#fff;border:0">📩 SMS gönder</button></div><button id="tp_ed" style="margin-top:10px;border:0;background:none;color:#2563eb;font-weight:700;cursor:pointer;padding:4px 0">✎ Şablonları düzenle</button></div>';
        m.querySelector('#tp_x').onclick = function () { m.remove(); };
        m.querySelector('#tp_c').onclick = function (e) { var b = e.target.closest('button[data-i]'); if (b) { cur = +b.getAttribute('data-i'); fill(); } };
        m.querySelector('#tp_wa').onclick = function () { window.open('https://wa.me/' + (waNum(phone) || '') + '?text=' + encodeURIComponent(m.querySelector('#tp_t').value), '_blank'); };
        m.querySelector('#tp_sms').onclick = function () { var b = this; b.disabled = true; call('POST', '/msg-templates/send', { job_id: jid, template_id: T[cur].id, channel: 'sms', text: m.querySelector('#tp_t').value }).then(function (r) { toast(r && r.status === 'sent' ? 'SMS gönderildi ✔' : 'SMS gönderilemedi: ' + ((r && r.error) || 'sağlayıcı ayarını kontrol edin')); }).catch(fail).then(function () { b.disabled = false; }); };
        m.querySelector('#tp_ed').onclick = edit; fill();
      }
      function edit() {
        var inp = 'width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:8px;font-size:13px;margin-bottom:6px';
        m.innerHTML = '<div style="width:100%;max-width:460px;max-height:92vh;overflow:auto;background:#fff;color:#0f172a;border-radius:14px;padding:20px;font-family:system-ui,sans-serif;position:relative"><button id="te_x" style="position:absolute;right:14px;top:12px;border:0;background:none;font-size:18px;cursor:pointer">✕</button><div style="font-size:17px;font-weight:800;margin-bottom:4px">✎ Mesaj şablonları</div><div style="font-size:12px;color:#64748b;margin-bottom:10px">Değişkenler: {ad} {usta} {link} {is_no} {zaman} {adres}</div><div id="te_l">' + T.map(function (x, i) { return '<div data-k="' + i + '" style="border:1px solid #e2e8f0;border-radius:10px;padding:10px;margin-bottom:8px"><input class="n" value="' + esc(x.name) + '" style="' + inp + ';font-weight:700"><textarea class="t" rows="3" style="' + inp + '">' + esc(x.text) + '</textarea><button type="button" class="r" style="border:0;background:none;color:#b91c1c;font-weight:700;cursor:pointer">Sil</button></div>'; }).join('') + '</div><div style="display:flex;gap:8px"><button id="te_a" style="' + bt + 'border:1px solid #cbd5e1;background:#fff">+ Yeni</button><button id="te_s" style="' + bt + 'flex:1;background:#0a1f44;color:#fff;border:0">Kaydet</button></div></div>';
        var rd = function () { return [].map.call(m.querySelectorAll('#te_l > div'), function (d, i) { return { id: (T[+d.getAttribute('data-k')] || {}).id, name: d.querySelector('.n').value, text: d.querySelector('.t').value }; }); };
        m.querySelector('#te_x').onclick = function () { m.remove(); };
        m.querySelector('#te_l').onclick = function (e) { if (e.target.classList.contains('r')) e.target.closest('[data-k]').remove(); };
        m.querySelector('#te_a').onclick = function () { var d = document.createElement('div'); d.setAttribute('data-k', 'n'); d.style.cssText = 'border:1px solid #e2e8f0;border-radius:10px;padding:10px;margin-bottom:8px'; d.innerHTML = '<input class="n" placeholder="Şablon adı" style="' + inp + ';font-weight:700"><textarea class="t" rows="3" placeholder="Mesaj metni" style="' + inp + '"></textarea><button type="button" class="r" style="border:0;background:none;color:#b91c1c;font-weight:700;cursor:pointer">Sil</button>'; m.querySelector('#te_l').appendChild(d); };
        m.querySelector('#te_s').onclick = function () { call('PUT', '/msg-templates', { templates: rd() }).then(function (r) { T = r.templates; cur = 0; toast('Şablonlar kaydedildi'); view(); }).catch(fail); };
      }
      document.body.appendChild(m); m.addEventListener('mousedown', function (e) { if (e.target === m) m.remove(); }); view();
    }).catch(fail);
  }
  function jobTplBtn() {
    var m = location.pathname.match(/^\/admin\/jobs\/([^\/?#]+)\/?$/), ex = document.getElementById('spx-tpl-btn');
    if (!m || document.body.classList.contains('spx-tech')) { if (ex) ex.remove(); return; }
    if (ex) return;
    var wa = document.getElementById('spx-wa-usta'); if (!wa || !wa.parentNode) return;
    var b = wa.cloneNode(true); b.id = 'spx-tpl-btn'; b.onclick = function (e) { e.preventDefault(); e.stopPropagation(); tplModal(m[1]); };
    var w = document.createTreeWalker(b, NodeFilter.SHOW_TEXT), n, done = false; while ((n = w.nextNode())) { if (!done && n.nodeValue.trim()) { n.nodeValue = 'Şablon / SMS'; done = true; } else if (done) n.nodeValue = ''; }
    if (!done) b.textContent = 'Şablon / SMS';
    b.style.setProperty('color', '#1d4ed8', 'important'); wa.parentNode.insertBefore(b, wa);
  }
  setInterval(jobTplBtn, 800);

  /* --- Usta: is listesi/detayini cevrimdisi okuma (son basarili yanit saklanir, baglanti yokken gosterilir) --- */
  (function () {
    var X = window.XMLHttpRequest; if (!X || X.prototype.__spxrc) return; X.prototype.__spxrc = 1;
    var op = X.prototype.open, sd = X.prototype.send, P = 'spx_rc:', MAXB = 900000, RCDOWN = 0;
    function uid() { try { return (me() || {}).id || 'u'; } catch (e) { return 'u'; } }
    function ok(u) { return /\/api\/jobs(\/[^\/?#]+)?(\?.*)?$/.test(u) && !/\/(pdf|photo|upload)/.test(u); }
    function key(u) { return P + uid() + ':' + String(u).replace(/^https?:\/\/[^\/]+/, ''); }
    function prune() { try { var ks = [], now = Date.now(); for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); if (k && k.indexOf(P) === 0) ks.push(k); } var rows = ks.map(function (k) { var t = 0; try { t = JSON.parse(localStorage.getItem(k)).t; } catch (e) { } return [k, t]; }).sort(function (a, b) { return b[1] - a[1]; }); rows.forEach(function (r, i) { if (i >= 30 || now - r[1] > 7 * 864e5) localStorage.removeItem(r[0]); }); } catch (e) { } }
    X.prototype.open = function (m, u) { this.__rc = { m: String(m).toUpperCase(), u: String(u) }; return op.apply(this, arguments); };
    X.prototype.send = function () {
      var q = this.__rc, self = this;
      if (q && /\/api\//.test(q.u) && document.body.classList.contains('spx-tech')) {
        self.addEventListener('error', function () { RCDOWN = Date.now(); }); self.addEventListener('timeout', function () { RCDOWN = Date.now(); });
        self.addEventListener('load', function () { if (self.status > 0) RCDOWN = 0; });
      }
      if (q && q.m === 'GET' && ok(q.u) && document.body.classList.contains('spx-tech')) {
        if (navigator.onLine === false || (RCDOWN && Date.now() - RCDOWN < 20000)) {
          var c = null; try { c = JSON.parse(localStorage.getItem(key(q.u)) || 'null'); } catch (e) { }
          if (c && c.b) {
            var rt = self.responseType, body = c.b, set = function (k, v) { try { Object.defineProperty(self, k, { value: v, configurable: true }); } catch (e) { } };
            setTimeout(function () {
              set('readyState', 4); set('status', 200); set('statusText', 'OK'); set('responseURL', q.u); set('responseText', rt === 'json' ? undefined : body); set('response', rt === 'json' ? JSON.parse(body) : body);
              self.getAllResponseHeaders = function () { return 'content-type: application/json\r\n'; }; self.getResponseHeader = function (h) { return /content-type/i.test(h) ? 'application/json' : null; };
              ['readystatechange', 'load', 'loadend'].forEach(function (t) { try { self.dispatchEvent(new Event(t)); } catch (e) { } });
            }, 0);
            return;
          }
        }
        self.addEventListener('load', function () { try { if (self.status === 200 && self.responseText && self.responseText.length < MAXB) { localStorage.setItem(key(q.u), JSON.stringify({ t: Date.now(), b: self.responseText })); } } catch (e) { prune(); } });
      }
      return sd.apply(this, arguments);
    };
    setTimeout(prune, 5000);
  })();

  /* Güncelleme 149: usta işi tamamlayınca PDF iner (mevcut), otomatik açılan "QR Etiket" penceresi açılmasın; elle "QR Etiket" butonu aynen çalışır */
  var NQ = { until: 0 };
  document.addEventListener('click', function (e) { var b = e.target.closest && e.target.closest('[data-testid="tech-qr-button"]'); if (b) NQ.until = 0; }, true);
  setInterval(function () {
    if (!document.body.classList.contains('spx-tech')) return;
    var t = document.querySelectorAll('[data-sonner-toast]');
    for (var i = 0; i < t.length; i++) { if (!t[i].__nq && /Servis tamamland/.test(t[i].textContent || '')) { t[i].__nq = 1; NQ.until = Date.now() + 30000; } }
    var d = NQ.until && Date.now() < NQ.until ? document.querySelector('[data-testid="qr-sticker-dialog"]') : null;
    if (d) { NQ.until = 0; d.style.display = 'none'; document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', keyCode: 27, bubbles: true })); setTimeout(function () { var o = document.querySelector('[data-testid="qr-sticker-dialog"]'); if (o) { var x = o.querySelector('button[aria-label="Close"],button.absolute'); if (x) x.click(); } }, 150); }
  }, 120);

  /* ===== Güncelleme 146: usta - garanti belgesi (mevcut PDF), müşteri imzası, fotoğraf uyarısı, yol tarifi, kazanç özeti, bildirim daveti, erişilebilirlik ===== */
  var TJ = { id: '', job: null, at: 0, bypass: false };
  function tjId() { var m = location.pathname.match(/^\/tech\/jobs\/([^\/?#]+)\/?$/); return m ? m[1] : ''; }
  function tjLoad(force) {
    var id = tjId(); if (!id) { TJ.id = ''; TJ.job = null; return; }
    if (TJ.id !== id) { TJ.id = id; TJ.job = null; TJ.at = 0; }
    if (!force && Date.now() - TJ.at < 4000) return; TJ.at = Date.now();
    call('GET', '/jobs/' + id).then(function (j) { if (TJ.id === id) TJ.job = j; }).catch(function () { });
  }
  function btnByText(root, re) { var l = (root || document).querySelectorAll('button'); for (var i = 0; i < l.length; i++) if (re.test((l[i].textContent || '').trim())) return l[i]; return null; }
  function sigPad(cv) {
    var c = cv.getContext('2d'), down = false, dirty = false; c.lineWidth = 3; c.lineCap = 'round'; c.strokeStyle = '#0f172a';
    function pt(e) { var r = cv.getBoundingClientRect(), t = e.touches ? e.touches[0] : e; return [(t.clientX - r.left) * cv.width / r.width, (t.clientY - r.top) * cv.height / r.height]; }
    function st(e) { e.preventDefault(); down = true; var p = pt(e); c.beginPath(); c.moveTo(p[0], p[1]); }
    function mv(e) { if (!down) return; e.preventDefault(); var p = pt(e); c.lineTo(p[0], p[1]); c.stroke(); dirty = true; }
    function en() { down = false; }
    cv.addEventListener('mousedown', st); cv.addEventListener('mousemove', mv); window.addEventListener('mouseup', en);
    cv.addEventListener('touchstart', st, { passive: false }); cv.addEventListener('touchmove', mv, { passive: false }); cv.addEventListener('touchend', en);
    return { clear: function () { c.clearRect(0, 0, cv.width, cv.height); dirty = false; }, empty: function () { return !dirty; }, blob: function (cb) { cv.toBlob(cb, 'image/png'); } };
  }
  function techJobExtras() {
    var id = tjId(), tech = document.body.classList.contains('spx-tech');
    if (!id || !tech) { ['spx-garanti', 'spx-yol', 'spx-sigcard'].forEach(function (k) { var o = document.getElementById(k); if (o) o.remove(); }); return; }
    var m = document.querySelector('main'); if (!m) return; var oc = document.getElementById('spx-sigcard'); if (oc) oc.remove();
    var gx = document.getElementById('spx-garanti'); if (gx) gx.remove();
    /* Yol tarifi */
    var ml = m.querySelector('a[href*="maps.google.com/?q="]'), y = document.getElementById('spx-yol');
    if (ml && !y) { var q = decodeURIComponent((ml.getAttribute('href').split('?q=')[1] || '')); y = document.createElement('a'); y.id = 'spx-yol'; y.className = 'notranslate'; y.target = '_blank'; y.rel = 'noopener'; y.href = 'https://www.google.com/maps/dir/?api=1&travelmode=driving&destination=' + encodeURIComponent(q); y.textContent = '🧭 Yol tarifi'; y.style.cssText = 'display:inline-block;margin:6px 0 0 8px;padding:6px 12px;border:1px solid #cbd5e1;border-radius:10px;font-size:13px;font-weight:600;color:#1155cc;background:#fff;text-decoration:none'; ml.parentNode.insertBefore(y, ml.nextSibling); }
  }
  setInterval(techJobExtras, 900);
  /* Kazanç özeti: /tech/balance */
  var ER = { busy: 0, at: 0, rows: null };
  function money(n) { return '₺' + (Math.round((n || 0) * 100) / 100).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function earnCard() {
    var ex = document.getElementById('spx-earn');
    if (!document.body.classList.contains('spx-tech') || location.pathname.replace(/\/$/, '') !== '/tech/balance') { if (ex) ex.remove(); return; }
    var m = document.querySelector('main'); if (!m) return;
    if (!ex) { ex = document.createElement('div'); ex.id = 'spx-earn'; ex.className = 'notranslate'; ex.style.cssText = 'margin:12px 0;background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:14px'; ex.innerHTML = '<b>Kazanç özeti</b><div id="spx-earn-b" style="margin-top:8px;color:#64748b;font-size:13px">Yükleniyor…</div>'; m.insertBefore(ex, m.firstChild); }
    if (ER.busy || (ER.rows && Date.now() - ER.at < 60000)) { if (ER.rows) earnPaint(); return; }
    ER.busy = 1; call('GET', '/jobs').then(function (d) { ER.rows = Array.isArray(d) ? d : (d.items || d.jobs || []); ER.at = Date.now(); earnPaint(); }).catch(function () { var b = document.getElementById('spx-earn-b'); if (b) b.textContent = 'Kazanç bilgisi alınamadı.'; }).then(function () { ER.busy = 0; });
  }
  function earnPaint() {
    var b = document.getElementById('spx-earn-b'); if (!b || !ER.rows) return;
    var now = new Date(), t0 = new Date(now.getFullYear(), now.getMonth(), now.getDate()), wd = (t0.getDay() + 6) % 7, w0 = new Date(t0.getTime() - wd * 864e5), m0 = new Date(now.getFullYear(), now.getMonth(), 1);
    var P = [['Bugün', t0], ['Bu hafta', w0], ['Bu ay', m0]], S = P.map(function () { return { n: 0, c: 0, k: 0 }; });
    ER.rows.forEach(function (j) { if (j.status !== 'tamamlandi' && j.status !== 'faturalandi') return; var d = new Date(j.completed_at || j.updated_at || 0); if (isNaN(d)) return; P.forEach(function (p, i) { if (d >= p[1]) { S[i].n++; S[i].c += +j.total_amount || 0; S[i].k += +j.technician_commission_amount || 0; } }); });
    b.style.color = ''; b.innerHTML = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">' + P.map(function (p, i) { return '<div style="background:#f8fafc;border-radius:12px;padding:10px;text-align:center"><div style="font-size:12px;color:#64748b">' + p[0] + '</div><div style="font-size:17px;font-weight:800;color:#15803d;margin:2px 0">' + money(S[i].k) + '</div><div style="font-size:11px;color:#64748b">' + S[i].n + ' iş · ciro ' + money(S[i].c) + '</div></div>'; }).join('') + '</div><div style="font-size:11px;color:#94a3b8;margin-top:6px">Kazanç = tamamlanan işlerde şirkete borç payı düşüldükten sonra size kalan tutar.</div>';
  }
  setInterval(earnCard, 1200);
  /* Bildirim daveti: /tech */
  function pushAsk() {
    var ex = document.getElementById('spx-pushask');
    var ok = document.body.classList.contains('spx-tech') && location.pathname.replace(/\/$/, '') === '/tech' && window.Notification && 'serviceWorker' in navigator && Notification.permission === 'default' && LS.get('spx_pushask', '') !== '1';
    if (!ok) { if (ex) ex.remove(); return; }
    if (ex) return; var m = document.querySelector('main'); if (!m) return;
    ex = document.createElement('div'); ex.id = 'spx-pushask'; ex.className = 'notranslate'; ex.style.cssText = 'margin:10px 0;background:#eff6ff;border:1px solid #bfdbfe;border-radius:14px;padding:12px;display:flex;gap:10px;align-items:center';
    ex.innerHTML = '<div style="flex:1;font-size:14px"><b>🔔 Yeni iş bildirimi</b><div style="font-size:12px;color:#475569">Size iş atanınca telefonunuza bildirim gelsin.</div></div><button type="button" id="spx-pa-y" style="border:0;background:#1155cc;color:#fff;border-radius:10px;padding:9px 14px;font-weight:700">Aç</button><button type="button" id="spx-pa-n" aria-label="Kapat" style="border:0;background:none;font-size:18px;color:#64748b">✕</button>';
    m.insertBefore(ex, m.firstChild);
    ex.querySelector('#spx-pa-n').onclick = function () { LS.set('spx_pushask', '1'); ex.remove(); };
    ex.querySelector('#spx-pa-y').onclick = function () { pushSub(true).then(function () { LS.set('spx_pushask', '1'); ex.remove(); toast('Bildirimler açık ✔'); }).catch(fail); };
  }
  setInterval(pushAsk, 1500);
  /* Erişilebilirlik: adı olmayan simge düğmelerine etiket */
  var AR = { x: 'Kapat', menu: 'Menü', search: 'Ara', plus: 'Ekle', trash: 'Sil', 'trash-2': 'Sil', pencil: 'Düzenle', edit: 'Düzenle', phone: 'Ara', bell: 'Bildirimler', 'chevron-left': 'Geri', 'chevron-right': 'İleri', 'arrow-left': 'Geri', eye: 'Göster', copy: 'Kopyala', download: 'İndir', upload: 'Yükle', 'refresh-cw': 'Yenile', settings: 'Ayarlar', camera: 'Kamera', mic: 'Mikrofon', check: 'Onayla', 'more-horizontal': 'Daha fazla', 'more-vertical': 'Daha fazla', filter: 'Filtrele', calendar: 'Takvim', user: 'Kullanıcı', 'log-out': 'Çıkış', moon: 'Koyu tema', sun: 'Açık tema', globe: 'Dil', languages: 'Dil', printer: 'Yazdır', send: 'Gönder', share: 'Paylaş' };
  function ariaFix() {
    var l = document.querySelectorAll('button:not([aria-label]):not([data-spxa]),a:not([aria-label]):not([data-spxa]),select:not([aria-label]):not([data-spxa]),input:not([aria-label]):not([data-spxa]):not([type=hidden]),textarea:not([aria-label]):not([data-spxa])'), n = 0;
    for (var i = 0; i < l.length && n < 120; i++, n++) {
      var e = l[i]; e.setAttribute('data-spxa', '1');
      if ((e.textContent || '').trim() || e.getAttribute('title') && e.tagName !== 'INPUT') { if (!(e.textContent || '').trim()) e.setAttribute('aria-label', e.getAttribute('title')); continue; }
      if (e.tagName === 'INPUT' || e.tagName === 'TEXTAREA' || e.tagName === 'SELECT') { if (e.id && document.querySelector('label[for="' + e.id + '"]') || e.closest('label')) continue; var nm = e.getAttribute('placeholder') || e.getAttribute('title') || (e.type === 'file' ? 'Dosya / fotoğraf seç' : e.type === 'search' ? 'Ara' : e.type === 'number' ? 'Tutar' : ''); if (nm) e.setAttribute('aria-label', nm); continue; }
      var sv = e.querySelector('svg'), cl = sv ? (sv.getAttribute('class') || '') : '', mm = cl.match(/lucide-([a-z0-9-]+)/), k = mm ? mm[1] : '';
      if (!k && e.getAttribute('data-testid')) k = e.getAttribute('data-testid');
      var lab = AR[k] || (/close|kapat/i.test(k) ? 'Kapat' : /menu/i.test(k) ? 'Menü' : /search/i.test(k) ? 'Ara' : '');
      if (lab) e.setAttribute('aria-label', lab);
    }
  }
  setInterval(ariaFix, 2500);

  /* ===== Usta: baglanti kesilince is guncellemelerini kuyruga al ve sonra gonder ===== */
  var OQ = { key: 'spx_oq' };
  function oqGet() { try { return JSON.parse(LS.get(OQ.key, '[]')) || []; } catch (e) { return []; } }
  function oqSet(a) { LS.set(OQ.key, JSON.stringify(a.slice(-40))); oqBanner(); }
  (function () {
    var X = window.XMLHttpRequest; if (!X || X.prototype.__spxq) return; X.prototype.__spxq = 1;
    var op = X.prototype.open, sh = X.prototype.setRequestHeader, sd = X.prototype.send;
    X.prototype.open = function (m, u) { this.__q = { m: String(m).toUpperCase(), u: String(u), h: {} }; return op.apply(this, arguments); };
    X.prototype.setRequestHeader = function (k, v) { if (this.__q) this.__q.h[k] = v; return sh.apply(this, arguments); };
    X.prototype.send = function (body) {
      var q = this.__q, self = this;
      if (q && q.m === 'PUT' && /\/api\/jobs\/[^\/?]+$/.test(q.u.split('?')[0]) && typeof body === 'string' && body.length < 1500000) {
        self.addEventListener('error', function () {
          if (!document.body.classList.contains('spx-tech') || self.status !== 0) return;
          var a = oqGet(); if (a.some(function (x) { return x.u === q.u && x.b === body; })) return;
          a.push({ u: q.u, b: body, h: q.h, t: Date.now() }); oqSet(a); toast('Bağlantı yok — işlem kuyruğa alındı, bağlantı gelince gönderilecek');
        });
      }
      return sd.apply(this, arguments);
    };
  })();
  var OQBUSY = false;
  function oqFlush() {
    var a = oqGet(); if (!a.length || OQBUSY || navigator.onLine === false) return; OQBUSY = true;
    var tok = LS.get('token', ''), ok = 0, failed = 0;
    (function next() {
      var cur = oqGet(); if (!cur.length) { OQBUSY = false; if (ok) toast(ok + ' bekleyen işlem gönderildi ✔'); if (failed) toast(failed + ' işlem sunucu tarafından reddedildi'); if (ok && /^\/tech\/jobs\//.test(location.pathname)) setTimeout(function () { location.reload(); }, 900); return; }
      var x = cur[0], h = {}; Object.keys(x.h || {}).forEach(function (k) { h[k] = x.h[k]; }); if (tok) h.Authorization = 'Bearer ' + tok;
      fetch(x.u, { method: 'PUT', headers: h, body: x.b }).then(function (r) {
        if (r.status === 401 || r.status === 403 || r.status >= 500) { OQBUSY = false; return; }          /* oturum/sunucu sorunu: sonra tekrar dene */
        var c = oqGet(); c.shift(); oqSet(c); if (r.ok) ok++; else failed++; next();
      }).catch(function () { OQBUSY = false; });
    })();
  }
  function oqBanner() {
    var n = oqGet().length, off = navigator.onLine === false, b = document.getElementById('spx-oq');
    if (!document.body.classList.contains('spx-tech') || (!n && !off)) { if (b) b.remove(); return; }
    if (!b) { b = document.createElement('div'); b.id = 'spx-oq'; b.className = 'notranslate'; b.style.cssText = 'position:fixed;left:8px;right:8px;bottom:78px;z-index:9997;background:#334155;color:#fff;border-radius:12px;padding:9px 12px;font-size:13px;font-weight:600;text-align:center'; document.body.appendChild(b); }
    var t = (off ? '📴 Çevrimdışı' : '🔄 Bağlantı var') + (n ? ' · ' + n + ' işlem gönderilmeyi bekliyor' : '');
    if (b.textContent !== t) b.textContent = t;
  }
  window.addEventListener('online', function () { oqBanner(); setTimeout(oqFlush, 800); });
  window.addEventListener('offline', oqBanner);
  setInterval(function () { oqBanner(); oqFlush(); }, 15000);


  /* ===== Yonetim > Ayarlar: "API & Entegrasyon Anahtarlari" merkezi (SMS, e-posta, odeme, pazaryeri, takip) ===== */
  var VMS = { busy: false };
  var HUB_OPT = { sandbox: 1, form_label: 1, order_label: 1, developer: 1, test_code: 1, from_sms: 1, from_whatsapp: 1, brand: 1, header: 1, source_addr: 1, port: 1, from_addr: 1 };
  var HUB_NOTIFY = [
    { id: 'verimor', name: 'Verimor SMS', grp: 'SMS / Mesaj', desc: 'Türkiye SMS gönderimi (usta atama, randevu hatırlatma, giriş bilgisi).', f: [['username', 'Kullanıcı adı (908501234567)', 0], ['password', 'API şifresi', 1], ['source_addr', 'Gönderici başlığı (onaylı)', 0]] },
    { id: 'netgsm', name: 'Netgsm SMS', grp: 'SMS / Mesaj', desc: 'Alternatif SMS sağlayıcısı.', f: [['usercode', 'Kullanıcı kodu', 0], ['password', 'Şifre', 1], ['header', 'Mesaj başlığı', 0]] },
    { id: 'twilio', name: 'Twilio (SMS + WhatsApp)', grp: 'SMS / Mesaj', desc: 'WhatsApp ve uluslararası SMS.', f: [['account_sid', 'Account SID', 0], ['auth_token', 'Auth Token', 1], ['from_sms', 'SMS gönderen no', 0], ['from_whatsapp', 'WhatsApp gönderen no', 0]] },
    { id: 'smtp', name: 'E-posta (SMTP)', grp: 'E-posta', desc: 'Haftalık rapor ve e-posta bildirimleri.', f: [['host', 'SMTP sunucusu', 0], ['port', 'Port (587)', 0], ['user', 'Kullanıcı', 0], ['password', 'Şifre', 1], ['from_addr', 'Gönderen adres', 0]] }
  ];
  var HUB_MODS = ['social', 'turnstile', 'iyzico', 'trendyol', 'hepsiburada', 'n11', 'ga4', 'ads', 'yandex', 'fb_pixel', 'fb_capi', 'merchant_api'];
  function settingsSms() {
    var pg = document.querySelector('[data-testid="settings-page"]'), ex = document.getElementById('spx-vmcard');
    if (!pg || !/^\/admin\/settings\/?$/.test(location.pathname) || document.body.classList.contains('spx-tech')) { if (ex) ex.remove(); return; }
    if (ex || VMS.busy) return;
    var ai = document.querySelector('[data-testid="ai-card"]'), host = ai; while (host && host.parentElement !== pg && host.parentElement) host = host.parentElement;
    if (!host || !host.parentElement) return;
    VMS.busy = true;
    Promise.all([call('GET', '/governance/notify-settings'), call('GET', '/admin/modules').catch(function () { return null; })]).then(function (z) {
      if (document.getElementById('spx-vmcard')) return;
      var c = z[0], M = z[1], mods = {}; if (M) M.modules.forEach(function (m) { mods[m.id] = m; });
      var inp = 'width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:9px 10px;font-size:14px;background:#fff;color:#0f172a';
      var lab = 'display:block;font-size:13px;font-weight:600;color:#334155;margin-bottom:4px';
      var btn = 'border:1px solid #cbd5e1;background:#fff;border-radius:10px;padding:9px 14px;font-weight:600;cursor:pointer;font-size:14px';
      var prim = 'border:0;background:#2563eb;color:#fff;border-radius:10px;padding:9px 16px;font-weight:700;cursor:pointer;font-size:14px';
      var filled = function (vals, fields, skip) { return fields.every(function (f) { return skip[f[0]] || (vals && vals[f[0]]); }); };
      var pillS = function (ok, on) { return '<span class="vm_pl" style="font-size:11px;font-weight:700;border-radius:99px;padding:2px 9px;white-space:nowrap;background:' + (ok ? (on === false ? '#fef3c7;color:#92400e' : '#dcfce7;color:#166534') : '#f1f5f9;color:#64748b') + '">' + (ok ? (on === false ? 'Girildi · kapalı' : 'Hazır') : 'Girilmedi') + '</span>'; };
      var secs = HUB_NOTIFY.map(function (n) { var vals = c[n.id] || {}; return { kind: 'n', id: n.id, name: n.name, grp: n.grp, desc: n.desc, f: n.f, vals: vals, ok: filled(vals, n.f, HUB_OPT), on: c.provider === n.id || n.id === 'smtp' ? undefined : (c.provider === n.id) }; });
      HUB_MODS.forEach(function (id) {
        var m = mods[id]; if (!m) return; var vals = ((M.config || {})[id]) || {}, f = m.fields.map(function (x) { return [x.key, x.label, x.secret ? 1 : 0]; });
        secs.push({ kind: 'm', id: id, name: m.label, grp: m.group, desc: m.desc, f: f, vals: vals, ok: filled(vals, f, HUB_OPT), on: m.enabled });
      });
      var d = document.createElement('div'); d.id = 'spx-vmcard'; d.className = 'notranslate'; d.setAttribute('data-testid', 'api-hub');
      d.style.cssText = 'background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:20px;color:#0f172a';
      var provSel = '<label style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:6px 0 14px;font-size:14px"><b>Aktif SMS sağlayıcısı:</b><select id="hub_prov" style="border:1px solid #cbd5e1;border-radius:8px;padding:7px 10px;font-size:14px;background:#fff">' + [['none', 'Kapalı (mesaj gitmez)'], ['verimor', 'Verimor'], ['netgsm', 'Netgsm'], ['twilio', 'Twilio'], ['webhook', 'Webhook (özel)']].map(function (o) { return '<option value="' + o[0] + '"' + (c.provider === o[0] ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select><button id="hub_provsave" style="' + btn + '">Seçimi kaydet</button></label>';
      var groups = []; secs.forEach(function (x) { if (groups.indexOf(x.grp) < 0) groups.push(x.grp); });
      d.innerHTML = '<b style="font-size:18px">🔑 API &amp; Entegrasyon Anahtarları</b><p style="color:#64748b;font-size:13px;margin:6px 0 4px">Sitedeki tüm dış bağlantıların anahtarları tek yerde: SMS, e-posta, ödeme (iyzico), pazaryerleri, Google/Meta takip. Şifre ve anahtarlar kaydedildikten sonra gizli görünür. Yapay zekâ anahtarı yukarıdaki "Yapay zekâ yardımcıları" kartındadır; Google Search Console/Ads bağlantısı Pazarlama Merkezi\'ndedir.</p>' + provSel + '<div id="hub_res" style="font-size:13px;margin-bottom:8px"></div>' +
        groups.map(function (g) {
          return '<div style="margin-top:10px"><div style="font-size:12px;font-weight:700;letter-spacing:.06em;color:#64748b;text-transform:uppercase;margin-bottom:6px">' + esc(g) + '</div>' + secs.filter(function (x) { return x.grp === g; }).map(function (x) {
            return '<details data-sec="' + x.kind + ':' + x.id + '" style="border:1px solid #e2e8f0;border-radius:12px;padding:10px 12px;margin-bottom:8px"><summary style="cursor:pointer;display:flex;gap:8px;align-items:center;justify-content:space-between;list-style:none"><span><b>' + esc(x.name) + '</b><br><small style="color:#64748b">' + esc(x.desc) + '</small></span>' + pillS(x.ok, x.on) + '</summary>' +
              '<div style="margin-top:12px;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px">' + x.f.map(function (f) { return '<label><span style="' + lab + '">' + esc(f[1]) + '</span><input data-k="' + f[0] + '" type="' + (f[2] ? 'password' : 'text') + '" autocomplete="' + (f[2] ? 'new-password' : 'off') + '" value="' + esc(x.vals[f[0]] == null ? '' : x.vals[f[0]]) + '" style="' + inp + '"></label>'; }).join('') + '</div>' +
              (x.kind === 'm' ? '<label style="display:flex;align-items:center;gap:8px;margin-top:12px;font-size:14px"><input type="checkbox" data-en' + (x.on ? ' checked' : '') + '> Bu entegrasyon açık</label>' : '') +
              '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px"><button data-save style="' + prim + '">Kaydet</button>' + (x.id === 'verimor' ? '<button data-vbal style="' + btn + '">Kontör sorgula</button><button data-vhd style="' + btn + '">Başlıklarımı listele</button>' : '') + '</div>' +
              (x.id === 'verimor' ? '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center"><input data-vt placeholder="Test numarası 05xx xxx xx xx" style="' + inp + ';max-width:240px"><button data-vtest style="' + btn + '">Test SMS gönder</button></div>' : '') +
              '<div data-r style="margin-top:8px;font-size:13px"></div></details>';
          }).join('') + '</div>';
        }).join('') + '<p style="color:#64748b;font-size:12px;margin:14px 0 0">Hangi olaylarda mesaj gideceği (müşteri, usta, randevu hatırlatma): <a href="#" id="vm_go" style="color:#2563eb;font-weight:600">Pazarlama &amp; İletişim → WhatsApp &amp; Bildirim</a>. Sunucu IP adresi Verimor OİM\'de izinli olmalıdır.</p>';
      host.parentElement.insertBefore(d, host.nextSibling);
      var say = function (el, t, ok) { el.innerHTML = '<b style="color:' + (ok ? '#15803d' : '#dc2626') + '">' + esc(t) + '</b>'; };
      var hres = d.querySelector('#hub_res');
      var find = function (key) { return secs.filter(function (x) { return x.kind + ':' + x.id === key; })[0]; };
      var collect = function (det) { var o = {}; Array.prototype.forEach.call(det.querySelectorAll('input[data-k]'), function (i) { o[i.getAttribute('data-k')] = i.value.trim(); }); return o; };
      var saveSec = function (det) {
        var x = find(det.getAttribute('data-sec')), vals = collect(det);
        if (x.kind === 'n') { var pl = {}; pl[x.id] = vals; return call('PUT', '/governance/notify-settings', pl).then(function (n) { c = n; x.vals = n[x.id] || {}; Array.prototype.forEach.call(det.querySelectorAll('input[data-k]'), function (i) { var v = x.vals[i.getAttribute('data-k')]; if (v != null) i.value = v; }); return n; }); }
        var cfg = {}; cfg[x.id] = vals; var fl = {}; fl[x.id] = det.querySelector('[data-en]').checked;
        return call('PUT', '/admin/modules', { flags: fl, config: cfg }).then(function (r) { x.vals = (r.config || {})[x.id] || {}; Array.prototype.forEach.call(det.querySelectorAll('input[data-k]'), function (i) { var v = x.vals[i.getAttribute('data-k')]; if (v != null) i.value = v; }); return r; });
      };
      var refreshPill = function (det) { var x = find(det.getAttribute('data-sec')), en = x.kind === 'm' ? det.querySelector('[data-en]').checked : (c.provider === x.id ? true : (x.id === 'smtp' ? undefined : false)); var ok = filled(x.vals, x.f, HUB_OPT), p = det.querySelector('.vm_pl'), t = document.createElement('div'); t.innerHTML = pillS(ok, en); p.replaceWith(t.firstChild); };
      d.addEventListener('click', function (e) {
        var det = e.target.closest('details[data-sec]'), r = det ? det.querySelector('[data-r]') : null;
        if (e.target.closest('#vm_go')) { e.preventDefault(); open('wa'); return; }
        if (e.target.closest('#hub_provsave')) { call('PUT', '/governance/notify-settings', { provider: d.querySelector('#hub_prov').value }).then(function (n) { c = n; say(hres, 'SMS sağlayıcısı kaydedildi ✔', true); Array.prototype.forEach.call(d.querySelectorAll('details[data-sec^="n:"]'), refreshPill); }).catch(function (er) { say(hres, er.message || 'Kaydedilemedi', false); }); return; }
        if (!det) return;
        if (e.target.closest('[data-save]')) { say(r, 'Kaydediliyor…', true); saveSec(det).then(function () { say(r, 'Kaydedildi ✔', true); refreshPill(det); }).catch(function (er) { say(r, er.message || 'Kaydedilemedi', false); }); }
        else if (e.target.closest('[data-vhd]')) { say(r, 'Başlıklar alınıyor…', true); saveSec(det).then(function () { return call('POST', '/governance/verimor-headers', {}); }).then(function (b) { var L = b.headers || []; if (!L.length) { say(r, 'Hesabınızda kayıtlı başlık görünmüyor — Verimor\'dan harfli bir başlık tanımlatın', false); return; } r.innerHTML = '<div style="margin-bottom:6px"><b>Hesabınızdaki başlıklar</b> (dokununca alana yazılır; <u>rakamlı başlıklar API\'de kullanılamaz</u>):</div>' + L.map(function (h) { var num = /^[0-9+\s]+$/.test(h); return '<button data-pickh="' + esc(h) + '" style="margin:0 6px 6px 0;border:1px solid ' + (num ? '#fca5a5;background:#fef2f2;color:#991b1b' : '#86efac;background:#f0fdf4;color:#166534') + ';border-radius:99px;padding:5px 12px;font-weight:700;cursor:pointer">' + esc(h) + (num ? ' ✖' : ' ✔') + '</button>'; }).join('') + '<div data-hm style="margin-top:4px"></div>'; }).catch(function (er) { say(r, er.message || 'Hata', false); }); }
        else if (e.target.closest('[data-pickh]')) { var hv = e.target.closest('[data-pickh]').getAttribute('data-pickh'), isn = /^[0-9+\s]+$/.test(hv); det.querySelector('[data-k=source_addr]').value = hv; say(det.querySelector('[data-hm]'), '“' + hv + '” alana yazıldı — Kaydet\'e basın' + (isn ? ' (rakamlı başlık; Verimor API reddederse harfli başlık gerekir)' : ''), !isn); }
        else if (e.target.closest('[data-vbal]')) { say(r, 'Sorgulanıyor…', true); saveSec(det).then(function () { return call('POST', '/governance/verimor-balance', {}); }).then(function (b) { say(r, 'Bağlantı tamam ✔ Kalan kontör: ' + b.balance, true); }).catch(function (er) { say(r, er.message || 'Hata', false); }); }
        else if (e.target.closest('[data-vtest]')) { var to = det.querySelector('[data-vt]').value.trim(); if (!to) { say(r, 'Test numarasını yazın', false); return; } say(r, 'Gönderiliyor…', true); saveSec(det).then(function () { return call('POST', '/governance/notify-test', { channel: 'sms', to: to }); }).then(function (b) { if (b.status === 'sent') say(r, 'SMS gönderildi ✔ (Verimor aktif sağlayıcı değilse üstten seçip kaydedin)', true); else say(r, 'Gönderilemedi: ' + (b.error || b.status), false); }).catch(function (er) { say(r, er.message || 'Hata', false); }); }
      });
    }).catch(function () { }).then(function () { VMS.busy = false; });
  }
  setInterval(settingsSms, 900);
  // ---- GUNCELLEME 139: Ayarlar sayfasi sekmeli (daha sade): Servis Fisi / Gizlilik / Mesaj & E-posta / Odeme & Pazaryeri / Site & Takip / Yapay Zeka
  var STB = [['fis', 'Servis Fişi'], ['giz', 'Gizlilik'], ['msg', 'Mesaj & E-posta'], ['pay', 'Ödeme & Pazaryeri'], ['site', 'Site & Takip'], ['ai', 'Yapay Zekâ']];
  function stGrp(t) {
    t = String(t || '').toLocaleLowerCase('tr');
    if (/sms|mesaj|e-posta|posta/.test(t)) return 'msg';
    if (/ödeme|pazaryeri/.test(t)) return 'pay';
    return 'site';
  }
  function settingsTabs() {
    var pg = document.querySelector('[data-testid="settings-page"]'), bar = document.getElementById('spx-stabs');
    if (!pg || !/^\/admin\/settings\/?$/.test(location.pathname) || document.body.classList.contains('spx-tech')) { if (bar) bar.remove(); var st0 = document.getElementById('spx-stcss'); if (st0) st0.remove(); return; }
    if (!document.getElementById('spx-stcss')) {
      var st = document.createElement('style'); st.id = 'spx-stcss';
      st.textContent = '[data-spxt]:not([data-spxt~="on"]){display:none!important}#spx-stabs{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 4px;padding:6px;background:#fff;border:1px solid #e2e8f0;border-radius:14px;position:sticky;top:8px;z-index:5}' +
        '#spx-stabs button{border:0;background:transparent;border-radius:10px;padding:9px 14px;font-weight:700;font-size:14px;color:#475569;cursor:pointer;flex:0 0 auto}#spx-stabs button:hover{background:#f1f5f9}#spx-stabs button.on{background:#2563eb;color:#fff}' +
        '#spx-stabs button i{font-style:normal;font-weight:600;font-size:11px;opacity:.7;margin-left:6px}.spx-dark #spx-stabs{background:#111c33;border-color:#1e2d4a}.spx-dark #spx-stabs button{color:#cbd5e1}.spx-dark #spx-stabs button.on{background:#2563eb;color:#fff}';
      document.head.appendChild(st);
    }
    var cur = LS.get('spx_settab', 'fis'); if (!STB.some(function (x) { return x[0] === cur; })) cur = 'fis';
    var head = pg.firstElementChild, cards = [].slice.call(pg.children).filter(function (e) { return e !== head && e.id !== 'spx-stabs'; });
    var tag = function (el, tab) { if (!el) return; el.setAttribute('data-spxt', tab + (tab === cur ? ' on' : '')); };
    cards.forEach(function (c) {
      if (c.id === 'spx-vmcard') {
        tag(c, 'hub');
        c.setAttribute('data-spxt', 'hub on'); // kutu hep acik; icerigi gruplara gore suzulur
        var kids = [].slice.call(c.children);
        kids.forEach(function (k) {
          var lab = k.querySelector && k.querySelector(':scope > div:first-child');
          var isGroup = k.tagName === 'DIV' && k.querySelector('details[data-sec]');
          var tab;
          if (isGroup) { tab = stGrp(lab ? lab.textContent : ''); }
          else if (k.id === 'hub_res' || k.tagName === 'LABEL' || k.tagName === 'P' || k.tagName === 'B') { tab = (k.tagName === 'B' || (k.tagName === 'P' && /Sitedeki tüm dış/.test(k.textContent))) ? 'hubhead' : 'msg'; }
          else tab = 'msg';
          if (tab === 'hubhead') k.setAttribute('data-spxt', 'on'); else k.setAttribute('data-spxt', tab + (tab === cur ? ' on' : ''));
        });
        return;
      }
      if (c.getAttribute('data-testid') === 'ai-card') { tag(c, 'ai'); return; }
      var t = (c.textContent || '').slice(0, 140);
      if (/PDF Tasarımı|Varsayılan PDF Notu|Firma Bilgileri|Fiyat Teklifi Alt Notu/.test(t)) tag(c, 'fis');
      else if (/Müşteri telefonunu ustadan gizle|Usta Ekranı Gizlilik Kuralları/.test(t)) tag(c, 'giz');
      else if (c.tagName === 'BUTTON') { c.setAttribute('data-spxt', 'on'); }
      else tag(c, cur === 'fis' ? 'fis' : 'zz');
    });
    // hub kutusu sadece mesaj/odeme/site sekmelerinde gorunsun
    var hub = document.getElementById('spx-vmcard'); if (hub) hub.setAttribute('data-spxt', (/^(msg|pay|site)$/.test(cur)) ? 'hub on' : 'hub');
    // sekme cubugu
    if (!bar) {
      bar = document.createElement('div'); bar.id = 'spx-stabs'; bar.className = 'notranslate'; bar.setAttribute('role', 'tablist');
      bar.onclick = function (e) { var b = e.target.closest('button[data-t]'); if (!b) return; LS.set('spx_settab', b.getAttribute('data-t')); settingsTabs(); window.scrollTo({ top: 0, behavior: 'smooth' }); };
      head.parentElement.insertBefore(bar, head.nextSibling);
    }
    var html = STB.map(function (x) { return '<button type="button" role="tab" data-t="' + x[0] + '" class="' + (x[0] === cur ? 'on' : '') + '">' + x[1] + '</button>'; }).join('');
    if (bar.getAttribute('data-h') !== html) { bar.innerHTML = html; bar.setAttribute('data-h', html); }
    // grup/alt elemanlari: aktif sekmeyi isaretle (tag fonksiyonu 'on' ekler)
    [].forEach.call(pg.querySelectorAll('[data-spxt]'), function (el) {
      var v = (el.getAttribute('data-spxt') || '').split(' ')[0];
      if (v === 'on' || v === 'hub') return;
      var on = v === cur; var want = v + (on ? ' on' : ''); if (el.getAttribute('data-spxt') !== want) el.setAttribute('data-spxt', want);
    });
  }
  setInterval(settingsTabs, 700);
  // ---- GUNCELLEME 140: yonetim paneli arama (Ctrl+K / "/" / sag ustteki dugme): sayfalar + servis kayitlari + musteriler + ustalar
  var PAL = { el: null, sel: 0, items: [], t: 0, tech: null, seq: 0 };
  function palIndex() {
    var out = [];
    MENU.forEach(function (g) { g[1].forEach(function (it) { if (!canMenu(it[0])) return; out.push({ k: 'p', t: it[1], s: g[0] || 'Panel', go: it[0] }); }); });
    Object.keys(SUB).forEach(function (p) { if (!canMenu(p)) return; var par = ''; MENU.forEach(function (g) { g[1].forEach(function (it) { if (it[0] === p) par = it[1]; }); }); SUB[p].forEach(function (x) { out.push({ k: 'p', t: par + ' › ' + x[1], s: 'Sekme', go: p + '?tab=' + x[0] }); }); });
    return out;
  }
  function palNorm(x) { return String(x || '').toLocaleLowerCase('tr').replace(/ı/g, 'i').replace(/ş/g, 's').replace(/ğ/g, 'g').replace(/ü/g, 'u').replace(/ö/g, 'o').replace(/ç/g, 'c').replace(/[^a-z0-9 ]/g, ' '); }
  function palGo(it) {
    palClose();
    if (it.k === 'p') { if (it.go.indexOf('ek:') === 0) { open(it.go.slice(3)); } else { if (ov) ov.classList.remove('on'); goto(it.go); } }
    else if (it.k === 'j') { if (ov) ov.classList.remove('on'); goto('/admin/jobs/' + it.id); }
    else if (it.k === 'c') { open('m360'); setTimeout(function () { m360Detail(it.phone || it.id); }, 80); }
    else if (it.k === 't') { if (ov) ov.classList.remove('on'); goto('/admin/technicians'); }
  }
  function palClose() { if (PAL.el) { PAL.el.remove(); PAL.el = null; } }
  function palRender() {
    var box = PAL.el && PAL.el.querySelector('#spx-pl'); if (!box) return;
    var groups = { p: 'Sayfalar', j: 'Servis kayıtları', c: 'Müşteriler', t: 'Ustalar' }, last = '', h = '';
    PAL.items.forEach(function (it, i) {
      if (it.k !== last) { h += '<div style="font:700 11px/1 Inter,system-ui;letter-spacing:.06em;color:#64748b;text-transform:uppercase;padding:10px 12px 4px">' + groups[it.k] + '</div>'; last = it.k; }
      h += '<div data-i="' + i + '" style="display:flex;justify-content:space-between;gap:10px;padding:9px 12px;border-radius:10px;cursor:pointer;' + (i === PAL.sel ? 'background:#eff6ff;' : '') + '"><span style="font-weight:600;color:#0f172a;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(it.t) + '</span><span style="color:#64748b;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:45%">' + esc(it.s || '') + '</span></div>';
    });
    box.innerHTML = h || '<div style="padding:18px 12px;color:#64748b;font-size:14px">Sonuç yok. Sayfa adı, iş no, müşteri adı/telefonu veya usta adı yazın.</div>';
    var a = box.querySelector('[data-i="' + PAL.sel + '"]'); if (a && a.scrollIntoView) a.scrollIntoView({ block: 'nearest' });
  }
  function palSearch(q) {
    var seq = ++PAL.seq, nq = palNorm(q).trim(), words = nq.split(/\s+/).filter(Boolean);
    var pages = !words.length ? palIndex().filter(function (x) { return x.s !== 'Sekme'; }).slice(0, 12) : palIndex().filter(function (x) { var n = palNorm(x.t + ' ' + x.s); return words.every(function (w) { return n.indexOf(w) >= 0; }); }).slice(0, 8);
    PAL.items = pages; PAL.sel = 0; palRender();
    if (nq.length < 2) return;
    var qq = q.trim();
    Promise.all([
      pcall('GET', '/jobs?q=' + encodeURIComponent(qq)).then(function (r) { return (Array.isArray(r) ? r : []).slice(0, 6).map(function (j) { return { k: 'j', id: j.id, t: (j.job_number || 'İş') + ' · ' + (j.customer_name || ''), s: [j.status, j.device_brand_name, j.customer_phone].filter(Boolean).join(' · ') }; }); }).catch(function () { return []; }),
      pcall('GET', '/customers?q=' + encodeURIComponent(qq)).then(function (r) { return (Array.isArray(r) ? r : []).slice(0, 5).map(function (c) { return { k: 'c', id: c.id, phone: c.phone, t: c.name || 'Müşteri', s: [c.phone, c.city].filter(Boolean).join(' · ') }; }); }).catch(function () { return []; }),
      (PAL.tech ? Promise.resolve(PAL.tech) : pcall('GET', '/technicians').then(function (r) { PAL.tech = Array.isArray(r) ? r : []; return PAL.tech; })).then(function (r) { return r.filter(function (t) { var n = palNorm((t.name || '') + ' ' + (t.phone || '') + ' ' + (t.email || '')); return words.every(function (w) { return n.indexOf(w) >= 0; }); }).slice(0, 4).map(function (t) { return { k: 't', id: t.id, t: t.name || 'Usta', s: [t.phone, t.city].filter(Boolean).join(' · ') }; }); }).catch(function () { return []; })
    ]).then(function (z) { if (seq !== PAL.seq || !PAL.el) return; PAL.items = pages.concat(z[0], z[1], z[2]); PAL.sel = 0; palRender(); });
  }
  function palOpen() {
    if (PAL.el || document.body.classList.contains('spx-tech') || !LS.get('token', '')) return;
    var d = document.createElement('div'); d.id = 'spx-pal'; d.className = 'notranslate';
    d.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(15,23,42,.45);display:flex;justify-content:center;align-items:flex-start;padding:8vh 12px 0';
    d.innerHTML = '<div style="width:100%;max-width:620px;background:#fff;border-radius:16px;box-shadow:0 24px 60px rgba(15,23,42,.35);overflow:hidden;font:14px/1.4 Inter,system-ui,sans-serif;color:#0f172a"><div style="display:flex;align-items:center;gap:10px;padding:12px 14px;border-bottom:1px solid #e2e8f0"><span style="font-size:18px">🔍</span><input id="spx-pq" type="search" autocomplete="off" placeholder="Sayfa, iş no, müşteri, telefon veya usta ara…" style="flex:1;border:0;outline:0;font-size:16px;background:transparent;color:#0f172a;min-width:0"><kbd style="font-size:11px;border:1px solid #cbd5e1;border-radius:6px;padding:2px 6px;color:#64748b">Esc</kbd></div><div id="spx-pl" style="max-height:60vh;overflow:auto;padding:4px 6px 8px"></div><div style="padding:8px 14px;border-top:1px solid #e2e8f0;font-size:12px;color:#64748b">↑↓ seç · Enter aç · Esc kapat · Ctrl+K her yerden</div></div>';
    d.onclick = function (e) { if (e.target === d) palClose(); var r = e.target.closest('[data-i]'); if (r) palGo(PAL.items[+r.getAttribute('data-i')]); };
    document.body.appendChild(d); PAL.el = d; PAL.sel = 0;
    var inp = d.querySelector('#spx-pq');
    inp.oninput = function () { clearTimeout(PAL.t); PAL.t = setTimeout(function () { palSearch(inp.value); }, 220); };
    inp.onkeydown = function (e) {
      if (e.key === 'Escape') { palClose(); }
      else if (e.key === 'ArrowDown') { e.preventDefault(); PAL.sel = Math.min(PAL.items.length - 1, PAL.sel + 1); palRender(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); PAL.sel = Math.max(0, PAL.sel - 1); palRender(); }
      else if (e.key === 'Enter') { e.preventDefault(); if (PAL.items[PAL.sel]) palGo(PAL.items[PAL.sel]); }
    };
    palSearch(''); setTimeout(function () { inp.focus(); }, 30);
  }
  document.addEventListener('keydown', function (e) {
    if (!/^\/admin/.test(location.pathname) && !(ov && ov.classList.contains('on'))) return;
    var tg = (e.target && e.target.tagName) || '', typing = /^(INPUT|TEXTAREA|SELECT)$/.test(tg) || (e.target && e.target.isContentEditable);
    if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); PAL.el ? palClose() : palOpen(); }
    else if (e.key === '/' && !typing && !e.ctrlKey && !e.metaKey && !e.altKey) { e.preventDefault(); palOpen(); }
  });
  function palBtn() {
    var b = document.getElementById('spx-pbtn'), on = /^\/admin/.test(location.pathname) && !document.body.classList.contains('spx-tech') && !!LS.get('token', '') && !/^\/admin\/login/.test(location.pathname);
    if (!on) { if (b) b.remove(); return; }
    if (b) return;
    b = document.createElement('button'); b.id = 'spx-pbtn'; b.type = 'button'; b.className = 'notranslate'; b.title = 'Ara (Ctrl+K)'; b.setAttribute('aria-label', 'Panelde ara');
    b.innerHTML = '<span style="font-size:16px">🔍</span><span class="spx-pbt" style="margin-left:6px;font-weight:600;font-size:13px">Ara</span><kbd class="spx-pbt" style="margin-left:8px;font-size:11px;border:1px solid #cbd5e1;border-radius:5px;padding:1px 5px;color:#64748b;font-family:inherit">Ctrl K</kbd>';
    b.style.cssText = 'position:fixed;right:54px;top:8px;z-index:9998;height:34px;display:flex;align-items:center;padding:0 10px;border-radius:8px;border:1px solid #cbd5e1;background:#fff;color:#0f172a;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.15)';
    b.onclick = palOpen; document.body.appendChild(b);
    if (!document.getElementById('spx-pbcss')) { var st = document.createElement('style'); st.id = 'spx-pbcss'; st.textContent = '#spx-pbtn{display:none!important}@media(max-width:700px){#spx-pbtn .spx-pbt{display:none}#spx-pbtn{width:34px;padding:0;justify-content:center}}.spx-dark #spx-pbtn{background:#111c33;color:#e2e8f0;border-color:#1e2d4a}'; document.head.appendChild(st); }
  }
  setInterval(palBtn, 800);




  /* ===== Yonetici icin 2FA (Authy) zorunlulugu: Guvenlik sayfasi karti + kurulum yonlendirmesi ===== */
  var TFP = { v: null, t: 0, busy: false };
  function tfaGuard() {
    if (!/^\/admin(\/|$)/.test(location.pathname) || document.body.classList.contains('spx-tech') || !LS.get('token', '')) { var b0 = document.getElementById('spx-tfb'); if (b0) b0.remove(); return; }
    if ((!TFP.v || Date.now() - TFP.t > 20000) && !TFP.busy) { TFP.busy = true; pcall('GET', '/auth/2fa/policy').then(function (r) { TFP.v = r; TFP.t = Date.now(); }).catch(function () { }).then(function () { TFP.busy = false; TFP.t = Date.now(); }); }
    var p = TFP.v, bar = document.getElementById('spx-tfb');
    if (!p || !p.must_setup) { if (bar) bar.remove(); return; }
    var path = location.pathname.replace(/\/$/, '');
    if (path !== '/admin/account') { goto('/admin/account'); return; }
    if (!bar) { bar = document.createElement('div'); bar.id = 'spx-tfb'; bar.className = 'notranslate'; bar.style.cssText = 'position:sticky;top:0;z-index:60;background:#b91c1c;color:#fff;padding:12px 14px;font-weight:700;font-size:14px;text-align:center;line-height:1.35'; bar.textContent = '🔐 Güvenlik gereği yönetici hesaplarında 2 adımlı doğrulama zorunlu. Aşağıdaki "2 adımlı doğrulama (2FA)" kartından Authy ile kurulumu tamamlayın; kurulana kadar diğer sayfalar kapalıdır.'; var m = document.querySelector('main') || document.body; m.insertBefore(bar, m.firstChild); }
  }
  setInterval(tfaGuard, 1500);
  var TFS = { busy: false };
  function secTfaCard() {
    var ex = document.getElementById('spx-tfcard');
    if (!/^\/admin\/security\/?$/.test(location.pathname) || document.body.classList.contains('spx-tech')) { if (ex) ex.remove(); return; }
    if (ex || TFS.busy) return; var m = document.querySelector('main'); var root = m && (m.firstElementChild || m); if (!root) return;
    TFS.busy = true;
    call('GET', '/governance/2fa-overview').then(function (r) {
      if (document.getElementById('spx-tfcard')) return;
      var d = document.createElement('div'); d.id = 'spx-tfcard'; d.className = 'notranslate'; d.setAttribute('data-testid', 'tfa-policy-card');
      d.style.cssText = 'background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:20px;margin-bottom:16px;color:#0f172a';
      var off = r.admins.filter(function (a) { return a.active && !a.enabled; }).length;
      d.innerHTML = '<div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center"><b style="font-size:17px">🔐 Yönetici 2 adımlı doğrulama (Authy)</b><span style="font-size:12px;font-weight:700;border-radius:99px;padding:3px 10px;background:' + (r.required ? '#dcfce7;color:#166534' : '#fef3c7;color:#92400e') + '">' + (r.required ? 'Zorunlu' : 'Zorunlu değil') + '</span></div>' +
        '<p style="color:#64748b;font-size:13px;margin:6px 0 10px">Açıkken, 2FA\'sı olmayan yönetici hesapları panelde yalnızca Hesabım sayfasına girebilir; Authy kurulumunu tamamlayana kadar diğer sayfalar kapalı kalır. Şifre ele geçirilse bile kod olmadan giriş yapılamaz.</p>' +
        r.admins.map(function (a) { return '<div style="display:flex;justify-content:space-between;gap:8px;padding:7px 0;border-top:1px solid #f1f5f9;font-size:14px"><span><b>' + esc(a.name || a.email) + '</b> <small style="color:#64748b">' + esc(a.email) + (a.active ? '' : ' · pasif') + '</small></span><span style="font-weight:700;color:' + (a.enabled ? '#15803d' : '#b91c1c') + '">' + (a.enabled ? '✔ Açık' : '✖ Kapalı') + '</span></div>'; }).join('') +
        '<label style="display:flex;align-items:center;gap:8px;margin-top:12px;font-size:14px"><input type="checkbox" id="tf_req"' + (r.required ? ' checked' : '') + '> Tüm yöneticiler için zorunlu kıl</label>' +
        (off && !r.required ? '<div style="margin-top:8px;font-size:12.5px;color:#92400e">⚠ ' + off + ' yönetici hesabında 2FA kapalı; zorunlu yaparsanız bu hesaplar ilk girişte kurulum yapmak zorunda kalır.</div>' : '') + '<div id="tf_res" style="margin-top:8px;font-size:13px"></div>';
      root.insertBefore(d, root.firstChild);
      d.querySelector('#tf_req').onchange = function () { var cb = this, want = cb.checked, res = d.querySelector('#tf_res'); call('PUT', '/governance/2fa-policy', { required: want }).then(function () { res.innerHTML = '<b style="color:#15803d">Kaydedildi ✔</b>'; TFP.t = 0; d.remove(); }).catch(function (e) { cb.checked = !want; res.innerHTML = '<b style="color:#dc2626">' + esc(e.message || 'Hata') + '</b>'; }); };
    }).catch(function () { }).then(function () { TFS.busy = false; });
  }
  setInterval(secTfaCard, 1000);


  /* ===== Giris ekraninda Cloudflare Turnstile (CAPTCHA) ===== */
  (function () {
    var CF = { tok: '', cfg: null, wid: null, busy: false, loaded: false };
    var isLogin = function () { return !!document.querySelector('input[type="password"]') && !document.querySelector('[data-testid="settings-page"]') && !/^\/admin\/(account|users)/.test(location.pathname) && /^\/(login|admin\/login|usta\/login|tech\/login|giris)?\/?$/i.test(location.pathname) || /login|giris/i.test(location.pathname) && !!document.querySelector('input[type="password"]'); };
    var xo = XMLHttpRequest.prototype.open, xs = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function (m, u) { this._cfl = /\/auth\/login(\?|$)/.test(String(u || '')) && String(m).toUpperCase() === 'POST'; return xo.apply(this, arguments); };
    XMLHttpRequest.prototype.send = function (b) {
      if (this._cfl && CF.tok && typeof b === 'string') { try { var j = JSON.parse(b); j.cf_token = CF.tok; b = JSON.stringify(j); } catch (e) { } this.addEventListener('loadend', function () { cfReset(); }); }
      return xs.call(this, b);
    };
    var of = window.fetch;
    if (of) window.fetch = function (u, o) {
      try { if (CF.tok && /\/auth\/login(\?|$)/.test(String(u && u.url || u)) && o && typeof o.body === 'string') { var j = JSON.parse(o.body); j.cf_token = CF.tok; o = Object.assign({}, o, { body: JSON.stringify(j) }); } } catch (e) { }
      return of.call(this, u, o);
    };
    function cfReset() { CF.tok = ''; try { if (window.turnstile && CF.wid != null) setTimeout(function () { window.turnstile.reset(CF.wid); }, 400); } catch (e) { } }
    function mount() {
      var pw = document.querySelector('input[type="password"]'); if (!pw || document.getElementById('spx-cf')) return;
      var form = pw.closest('form'); var box = document.createElement('div'); box.id = 'spx-cf'; box.style.cssText = 'margin:12px 0;display:flex;justify-content:center;min-height:65px';
      var btn = form && form.querySelector('button[type="submit"],button:not([type])');
      if (btn && btn.parentElement) btn.parentElement.insertBefore(box, btn); else if (form) form.appendChild(box); else return;
      var go = function () { try { CF.wid = window.turnstile.render(box, { sitekey: CF.cfg.site_key, callback: function (t) { CF.tok = t; }, 'expired-callback': function () { CF.tok = ''; }, 'error-callback': function () { CF.tok = ''; } }); } catch (e) { } };
      if (window.turnstile) go(); else if (!CF.loaded) { CF.loaded = true; var sc = document.createElement('script'); sc.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'; sc.async = true; sc.onload = go; document.head.appendChild(sc); } else setTimeout(function () { if (window.turnstile) go(); }, 800);
    }
    setInterval(function () {
      var ex = document.getElementById('spx-cf');
      if (!document.querySelector('input[type="password"]') || !isLogin()) { if (ex) { ex.remove(); CF.wid = null; CF.tok = ''; } return; }
      if (CF.cfg === null) { if (CF.busy) return; CF.busy = true; fetch(location.origin + '/api/auth/captcha-config').then(function (r) { return r.json(); }).then(function (j) { CF.cfg = j && j.enabled ? j : false; CF.busy = false; }).catch(function () { CF.cfg = null; CF.busy = false; setTimeout(function () { }, 0); }); return; }
      if (CF.cfg && !ex) mount();
    }, 1000);
  })();


  /* ===== Usta ekrani: Daha sayfasinda "Sik Sorulan Sorular" (Egitimler kartinin altinda) ===== */
  var FAQ = [["Giriş ve hesap", [["Giriş bilgilerim nerede? Şifremi unuttum.", "Hesabınız açılınca giriş bilgileriniz telefonunuza mesajla gönderilir. Bulamıyorsanız veya şifrenizi unuttuysanız merkezi arayın ya da yönetime yazın; giriş bilgisi yeniden gönderilir."], ["Telefon numaramı veya IBAN'ımı nasıl güncellerim?", "Daha → Profilim bölümünden IBAN ve bilgilerinizi girebilirsiniz. Telefon numarası değişirse yönetime bildirin; mesajlar kayıtlı numaraya gider."]]], ["Görevler ve iş akışı", [["Yeni iş atandı ama bildirim gelmedi.", "Üstteki zil (🔔) düğmesine dokunup bildirim iznini verdiğinizden emin olun. Telefonun ayarlarında tarayıcı/uygulama bildirimleri kapalı olmasın. Bildirim gelmese de Görevler ekranı birkaç saniyede bir yenilenir ve yeni iş orada görünür."], ["İşlerim listede görünmüyor.", "İş size atanmamış olabilir; yönetimden kontrol isteyin. Ayrıca yönetim iş kayıtlarını belirli saat aralıklarında gizleyebilir; aralık dışında kayıtlar yeniden görünür."], ["\"Yoldayım\" ile \"Yola Çık\" farkı nedir?", "\"Yoldayım\": müşteriye \"usta yolda\" mesajı ve canlı takip linki gönderir, tahmini varış süresini seçersiniz. \"Yola Çık\": işin durumunu Yolda yapar. Müşteriye vardığınızda \"Servise Başla\" ile durum Başladı olur."], ["Müşterinin telefonu neden yıldızlı görünüyor?", "Yönetim numarayı gizli tutacak şekilde ayarlamış olabilir. Arama düğmesine bastığınızda numara o an açılır. Her açış kaydedilir ve günlük bir sınır vardır."], ["Müşteriye ulaşamıyorum, ne yapmalıyım?", "Önce \"Müşteriye mesaj\" ile yazın ve arayın. Yine ulaşamazsanız Sohbet bölümünden merkeze durumu bildirin."], ["Müşteri indirim istiyor.", "İndirim talebini Sohbet bölümünden merkeze iletin."], ["İşi yanlış tamamladım, düzeltebilir miyim?", "Tamamlanan işi usta düzenleyemez. Sohbet'ten yönetime hangi kaydın neden düzeltileceğini yazın."], ["\"Tamamla\"ya basınca uyarı çıkıyor.", "Ekrandaki uyarı neyin eksik olduğunu söyler. Sık görülenler: işaretlenmemiş zorunlu kontrol listesi maddesi, kurulum işlerinde \"Sonra\" fotoğrafının olmaması. Eksiği tamamlayıp tekrar deneyin."]]], ["Parça, fotoğraf ve atölye", [["Stokta olmayan parçayı nasıl eklerim?", "Yedek Parçalar → Ekle'de \"Manuel\" seçip parçanın adını ve fiyatını yazın."], ["Fotoğraf yüklenmiyor.", "İnternet bağlantınızı kontrol edip tekrar deneyin; fotoğrafları teker teker ekleyin. Fotoğraflar sistem tarafından otomatik küçültülür, bu yüzden büyük dosyalar sorun olmaz. Bağlantı yoksa internet geldikten sonra yeniden yükleyin."], ["Atölyeye Al düğmesini göremiyorum.", "Düğme yalnızca iş \"Başladı\" durumundayken ve sayfanın altında, Müşteri Vazgeçti düğmesinin üstünde görünür. Önce \"Servise Başla\"ya basmış olmanız gerekir."], ["Atölyedeki cihazı nerede görürüm?", "Ana ekranda Atölye sekmesinde. Orada formu yazdırabilir, \"Hazır\" ve \"Teslim edildi\" işaretleyebilirsiniz."], ["QR Etiket ne işe yarar?", "Cihaza yapıştırılacak etiketi yazdırır. Müşteri etiketi telefonuyla okutarak cihazın servis geçmişini ve garanti durumunu görür, yeni servis talebi oluşturabilir."]]], ["Bakiye ve puan", [["Bakiyem neyi gösteriyor, ödemeyi nasıl yaparım?", "Şirkete olan borcunuzu, borç oranınızı ve şirket IBAN bilgisini gösterir. Havale/EFT yaptıktan sonra \"Ödeme yaptım\"a basarak yönetime haber verin. Ödeme yönetimde işlenince bakiyeniz düşer."], ["Puanım nasıl hesaplanıyor?", "Puan 0-100 arasıdır ve son 90 günü kapsar: müşteri puanı (30), tamamlama (15), tekrar arıza olmaması (15), hız (10), dakiklik (10), fotoğraf ve imza düzeni (10), nezaket (5), kasa disiplini (5). Seviyeniz ilk 5 tamamlanan işten sonra belirlenir."], ["Eğitimlerde \"Okudum\"a basmak zorunlu mu?", "Zorunlu etiketli modüllerin tamamlanması beklenir; diğerleri bilgi amaçlıdır. Okuduklarınız kaydedilir."]]], ["Telefon ve ekran", [["İnternet kesildi, yaptıklarım kaybolur mu?", "Hayır. Sayfa açıkken internet kesilirse üstte \"Çevrimdışı\" şeridi çıkar; iş formundaki kayıtlar cihazda bekler ve bağlantı gelince otomatik gönderilir. Uygulamayı internetsiz sıfırdan açmak bu kapsamda değildir."], ["Yazılar çok küçük, nasıl büyütürüm?", "Daha sayfasının en altındaki Yazı boyutu kartında A+ ile büyütebilirsiniz. Ayar bu cihazda saklanır."], ["Koyu tema ve dil nasıl değişir?", "Üstteki ay/güneş düğmesi temayı, dil düğmesi dili değiştirir."], ["Arıza kodunu bilmiyorum.", "Ana ekrandaki Arıza Asistanı'nı veya Daha → Arıza Rehberi'ni açın. Kodu ya da belirtiyi yazarak olası neden ve çözüm önerilerine ulaşırsınız."]]]];
  function techFaq() {
    var ex = document.getElementById('spx-faq');
    if (!document.body.classList.contains('spx-tech') || location.pathname.replace(/\/$/, '') !== '/tech/more') { if (ex) ex.remove(); return; }
    if (ex) return; var host = document.querySelector('[data-testid="tech-more"]'); if (!host) return;
    var tr = host.querySelector('[data-testid="training-card"]');
    var st = document.getElementById('spx-faq-css');
    if (!st) { st = document.createElement('style'); st.id = 'spx-faq-css'; st.textContent = '#spx-faq .fq-g{font-size:12px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.04em;margin:14px 0 4px}#spx-faq details{border-top:1px solid #e2e8f0;padding:2px 0}#spx-faq summary{cursor:pointer;list-style:none;padding:10px 22px 10px 0;font-size:14px;font-weight:600;position:relative;color:#0f172a}#spx-faq summary::-webkit-details-marker{display:none}#spx-faq summary::after{content:"+";position:absolute;right:2px;top:8px;font-size:18px;color:#64748b}#spx-faq details[open] summary::after{content:"\\2212"}#spx-faq .fq-a{font-size:13px;line-height:1.55;color:#334155;padding:0 0 12px;white-space:pre-wrap}#spx-faq input{width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:10px;padding:9px 11px;font-size:14px;margin-top:8px;background:#fff;color:#0f172a}'; document.head.appendChild(st); }
    ex = document.createElement('div'); ex.id = 'spx-faq'; ex.className = ((tr && tr.className) || 'rounded-xl border bg-card p-4 shadow-none border-slate-200') + ' notranslate'; ex.setAttribute('data-testid', 'faq-card');
    ex.innerHTML = '<div class="font-semibold">Sık Sorulan Sorular</div><div style="font-size:12px;color:#64748b;margin-top:2px">Usta ekranının nasıl kullanıldığına dair kısa yanıtlar.</div><input type="search" id="spx-faq-q" placeholder="Soru ara…">' +
      FAQ.map(function (g) { return '<div class="fq-gw"><div class="fq-g">' + esc(g[0]) + '</div>' + g[1].map(function (q) { return '<details data-q="' + esc((q[0] + ' ' + q[1]).toLowerCase()) + '"><summary>' + esc(q[0]) + '</summary><div class="fq-a">' + esc(q[1]) + '</div></details>'; }).join('') + '</div>'; }).join('') +
      '<div id="spx-faq-none" style="display:none;font-size:13px;color:#64748b;padding:10px 0">Sonuç bulunamadı. Sohbet bölümünden merkeze yazabilirsiniz.</div>';
    if (tr && tr.parentNode) tr.parentNode.insertBefore(ex, tr.nextSibling); else host.insertBefore(ex, host.firstChild.nextSibling || null);
    ex.querySelector('#spx-faq-q').oninput = function () {
      var v = this.value.trim().toLowerCase(), n = 0;
      [].forEach.call(ex.querySelectorAll('details'), function (d) { var ok = !v || d.getAttribute('data-q').indexOf(v) >= 0; d.style.display = ok ? '' : 'none'; if (ok) n++; });
      [].forEach.call(ex.querySelectorAll('.fq-gw'), function (g) { g.style.display = [].some.call(g.querySelectorAll('details'), function (d) { return d.style.display !== 'none'; }) ? '' : 'none'; });
      ex.querySelector('#spx-faq-none').style.display = n ? 'none' : 'block';
    };
  }
  setInterval(techFaq, 1000);

  // ---- GUNCELLEME 128: Sik Sorulan Sorular tek dugme + tam ekran pencere
  var FQX = false;
  function faqBtn() {
    var more = location.pathname.replace(/\/$/, '') === '/tech/more', old = document.getElementById('spx-faq'), bt = document.getElementById('spx-faqbtn');
    if (!document.body.classList.contains('spx-tech') || !more) { if (bt) bt.remove(); return; }
    if (!FQX) { FQX = true; FAQ.forEach(function (g) { if (/puan/i.test(g[0]) && !g[1].some(function (q) { return /Hizmet puan/.test(q[0]); })) g[1].push(['Hizmet puanım nasıl hesaplanır?', 'Son 180 günde tamamladığınız işlerden 5 üzerinden hesaplanır: müşteri yorumları %35, işe gitme hızı %25, müşteriyi arama hızı %20, işi bitirme hızı %20. Puanınızı Daha → profilinizde ve sertifikanızda görürsünüz. 15 dakika içinde aramak, randevuya zamanında gitmek ve işi makul sürede bitirmek puanınızı yükseltir. Ayrıntı: servisplus.net.tr/hizmet-puani/']); }); }
    if (old) old.style.display = 'none';
    if (!old) return;
    if (!bt) {
      bt = document.createElement('button'); bt.id = 'spx-faqbtn'; bt.type = 'button'; bt.className = 'notranslate'; bt.style.cssText = 'display:flex;align-items:center;gap:12px;width:100%;text-align:left;background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:14px;font:inherit;cursor:pointer;margin-bottom:12px';
      var n = FAQ.reduce(function (t, g) { return t + g[1].length; }, 0);
      bt.innerHTML = '<span style="font-size:24px">❓</span><span style="flex:1"><b style="font-size:15px;display:block">Sık Sorulan Sorular</b><span style="font-size:12.5px;color:#64748b">' + n + ' kısa yanıt · arama yapabilirsiniz</span></span><span style="color:#94a3b8;font-size:18px">›</span>';
      bt.onclick = faqOpen; old.parentNode.insertBefore(bt, old);
    }
  }
  setInterval(faqBtn, 900);
  function faqOpen() {
    if (document.getElementById('spx-faqov')) return;
    var ov = document.createElement('div'); ov.id = 'spx-faqov'; ov.className = 'notranslate'; ov.style.cssText = 'position:fixed;inset:0;z-index:99997;background:#f1f5f9;display:flex;flex-direction:column';
    ov.innerHTML = '<div style="display:flex;gap:8px;align-items:center;padding:10px 12px;background:#fff;border-bottom:1px solid #e2e8f0"><button data-a="x" style="border:1px solid #cbd5e1;background:#fff;border-radius:10px;padding:9px 14px;font-weight:700;font-size:14px">← Geri</button><div style="flex:1;font-weight:800;font-size:15px;text-align:center">Sık Sorulan Sorular</div><span style="min-width:70px"></span></div>' +
      '<div style="padding:10px 12px 0"><input id="spx-faqq" type="search" placeholder="Soru ara…" style="width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:12px;padding:11px 13px;font-size:15px;background:#fff"></div><div id="spx-faql" style="flex:1;overflow:auto;padding:10px 12px 20px;-webkit-overflow-scrolling:touch"></div>';
    document.body.appendChild(ov);
    var open = {}, L = ov.querySelector('#spx-faql'), qi = ov.querySelector('#spx-faqq');
    function paint() {
      var v = qi.value.trim().toLowerCase(), n = 0;
      L.innerHTML = FAQ.map(function (g, gi) {
        var rows = g[1].map(function (q, i) { return [q, gi + '_' + i]; }).filter(function (x) { return !v || (x[0][0] + ' ' + x[0][1]).toLowerCase().indexOf(v) >= 0; });
        if (!rows.length) return ''; n += rows.length;
        return '<div style="font-size:12px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.04em;margin:12px 4px 6px">' + esc(g[0]) + '</div>' + rows.map(function (x) {
          var o = !!open[x[1]] || !!v; return '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;margin-bottom:8px;overflow:hidden"><div data-a="tg" data-id="' + x[1] + '" style="display:flex;gap:10px;align-items:center;padding:13px 14px;cursor:pointer"><b style="flex:1;font-size:14px;line-height:1.35">' + esc(x[0][0]) + '</b><span style="color:#64748b;font-size:18px">' + (o ? '−' : '+') + '</span></div>' + (o ? '<div style="padding:0 14px 14px;font-size:13.5px;line-height:1.6;color:#334155;white-space:pre-wrap">' + esc(x[0][1]) + '</div>' : '') + '</div>';
        }).join('');
      }).join('') || '<div style="color:#64748b;padding:20px;text-align:center">Sonuç bulunamadı. Sohbet bölümünden merkeze yazabilirsiniz.</div>';
    }
    ov.onclick = function (e) { var t = e.target.closest && e.target.closest('[data-a]'); if (!t) return; if (t.getAttribute('data-a') === 'x') ov.remove(); else { var id = t.getAttribute('data-id'); open[id] = !open[id]; paint(); } };
    qi.oninput = paint; paint();
  }


  /* ===== Usta: ilk giriste KVKK aydinlatma + iletisim izni onayi ===== */
  var CNS = { busy: false, done: false, show: false };
  function consentCheck() {
    if (CNS.done || CNS.busy || !document.body.classList.contains('spx-tech') || !LS.get('token', '')) return;
    CNS.busy = true;
    call('GET', '/tech/consent').then(function (c) {
      CNS.busy = false;
      if (c.accepted) { CNS.done = true; return; }
      CNS.show = true; consentModal(c);
    }).catch(function () { CNS.busy = false; });
  }
  function consentModal(c) {
    if (document.getElementById('spx-cns')) return;
    var d = document.createElement('div'); d.id = 'spx-cns'; d.className = 'notranslate';
    d.style.cssText = 'position:fixed;inset:0;z-index:100000;background:rgba(15,23,42,.72);display:flex;align-items:center;justify-content:center;padding:14px';
    var T = c.texts || {};
    d.innerHTML = '<div style="background:#fff;border-radius:18px;max-width:480px;width:100%;max-height:92vh;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 20px 50px rgba(0,0,0,.35)">' +
      '<div style="padding:16px 18px 10px;border-bottom:1px solid #e2e8f0"><div style="font-size:18px;font-weight:800;color:#0f172a">Hoş geldiniz</div><div style="font-size:13px;color:#64748b;margin-top:3px">' + esc(T.firma || 'ServisPlus') + ' usta paneline devam etmeden önce lütfen aşağıdaki bilgilendirmeyi okuyup onaylayın.</div></div>' +
      '<div style="padding:12px 18px;overflow:auto;flex:1">' +
      '<div style="font-size:13px;font-weight:700;color:#0f172a;margin-bottom:4px">Kişisel Verilerin Korunması – Aydınlatma Metni</div>' +
      '<div style="font-size:12.5px;line-height:1.55;color:#334155;white-space:pre-wrap;border:1px solid #e2e8f0;border-radius:10px;padding:10px;max-height:34vh;overflow:auto;background:#f8fafc">' + esc(T.kvkk || '') + '</div>' +
      '<div style="font-size:13px;font-weight:700;color:#0f172a;margin:12px 0 4px">İletişim İzni</div>' +
      '<div style="font-size:12.5px;line-height:1.55;color:#334155;border:1px solid #e2e8f0;border-radius:10px;padding:10px;background:#f8fafc">' + esc(T.iletisim || '') + '</div>' +
      '<div style="font-size:13px;font-weight:700;color:#0f172a;margin:12px 0 4px">Usta Kuralları ve Hizmet Puanı</div>' +
      '<div style="font-size:12.5px;line-height:1.55;color:#334155;white-space:pre-wrap;border:1px solid #e2e8f0;border-radius:10px;padding:10px;max-height:34vh;overflow:auto;background:#f8fafc">' + esc(T.kurallar || '') + '</div>' +
      '<label style="display:flex;gap:9px;align-items:flex-start;margin-top:12px;font-size:13px;color:#0f172a"><input type="checkbox" id="cns_a" style="margin-top:3px;width:18px;height:18px;flex:none"><span>Aydınlatma metnini okudum ve anladım.</span></label>' +
      '<label style="display:flex;gap:9px;align-items:flex-start;margin-top:8px;font-size:13px;color:#0f172a"><input type="checkbox" id="cns_b" style="margin-top:3px;width:18px;height:18px;flex:none"><span>Yukarıdaki iletişim iznini onaylıyorum.</span></label>' +
      '<label style="display:flex;gap:9px;align-items:flex-start;margin-top:8px;font-size:13px;color:#0f172a"><input type="checkbox" id="cns_c" style="margin-top:3px;width:18px;height:18px;flex:none"><span>Usta kurallarını ve hizmet puanı sistemini okudum, kabul ediyorum.</span></label>' +
      '<div id="cns_m" style="font-size:12.5px;margin-top:8px;color:#dc2626;min-height:16px"></div></div>' +
      '<div style="padding:12px 18px;border-top:1px solid #e2e8f0;display:flex;gap:10px;align-items:center"><button id="cns_x" type="button" style="border:0;background:none;color:#64748b;font-size:13px;padding:8px 4px">Çıkış yap</button><button id="cns_ok" type="button" disabled style="flex:1;border:0;background:#2563eb;color:#fff;border-radius:12px;padding:12px;font-weight:700;font-size:15px;opacity:.45">Onaylıyorum ve devam et</button></div></div>';
    document.body.appendChild(d);
    var a = d.querySelector('#cns_a'), b = d.querySelector('#cns_b'), cc = d.querySelector('#cns_c'), ok = d.querySelector('#cns_ok');
    var upd = function () { var on = a.checked && b.checked && cc.checked; ok.disabled = !on; ok.style.opacity = on ? '1' : '.45'; };
    a.onchange = b.onchange = cc.onchange = upd;
    d.querySelector('#cns_x').onclick = function () { try { LS.set('token', ''); localStorage.removeItem('token'); localStorage.removeItem('user'); } catch (e) { } location.href = '/login'; };
    ok.onclick = function () {
      ok.disabled = true; ok.textContent = 'Kaydediliyor…';
      call('POST', '/tech/consent', { kvkk: true, contact: true, rules: true }).then(function () { CNS.done = true; CNS.show = false; d.remove(); toast('Teşekkürler, onayınız kaydedildi'); })
        .catch(function (e) { ok.disabled = false; ok.textContent = 'Onaylıyorum ve devam et'; d.querySelector('#cns_m').textContent = (e && e.message) || 'Kaydedilemedi, tekrar deneyin'; });
    };
  }
  setInterval(consentCheck, 1500);

  /* ===== Usta (Android): "Uygulamayi indir" - ana ekrana simge ekler; rahatsiz etmeyen hatirlatma ===== */
  var PWA = { ev: null, shown: false };
  var pwaGet = function () { try { return JSON.parse(LS.get('spx_pwa', '{}')) || {}; } catch (e) { return {}; } };
  var pwaSet = function (o) { LS.set('spx_pwa', JSON.stringify(o)); };
  var pwaAndroid = function () { return /android/i.test(navigator.userAgent || ''); };
  var pwaIOS = function () { var u = navigator.userAgent || ''; return /iphone|ipad|ipod/i.test(u) || (/Macintosh/.test(u) && navigator.maxTouchPoints > 1); };
  var pwaStandalone = function () { try { return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true; } catch (e) { return false; } };
  window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); PWA.ev = e; });
  window.addEventListener('appinstalled', function () { var o = pwaGet(); o.installed = 1; pwaSet(o); PWA.ev = null; var b = document.getElementById('spx-pwa'); if (b) b.remove(); var c = document.getElementById('spx-pwa-card'); if (c) c.remove(); toast('Uygulama yüklendi ✔ Ana ekranınızda ServisPlus simgesini bulabilirsiniz'); });
  function pwaSteps() {
    var d = document.createElement('div'); d.id = 'spx-pwa-steps'; d.className = 'notranslate';
    d.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(15,23,42,.6);display:flex;align-items:flex-end;justify-content:center';
    d.innerHTML = '<div style="background:#fff;border-radius:18px 18px 0 0;width:100%;max-width:520px;padding:18px 18px 22px"><div style="font-size:17px;font-weight:800;color:#0f172a">Ana ekrana ekleyin</div>' +
      '<ol style="margin:10px 0 0 18px;padding:0;font-size:14px;line-height:1.7;color:#334155">' + (pwaIOS() ? '<li>Safari\'de alttaki <b>Paylaş</b> düğmesine <b>(▯↑ kare ve yukarı ok)</b> dokunun. Düğmeyi göremiyorsanız ekranı hafifçe yukarı kaydırın.</li><li>Açılan listeyi yukarı kaydırıp <b>“Ana Ekrana Ekle”</b> seçeneğine dokunun.</li><li>Sağ üstteki <b>Ekle</b>\'ye dokunun. ServisPlus simgesi ana ekranınızda belirir.</li></ol><div style="margin-top:8px;font-size:12px;color:#64748b">Not: iPhone\'da bu işlem yalnızca <b>Safari</b> (veya iOS 16.4+ ile Chrome) tarayıcısında yapılır.</div>' : '<li>Tarayıcının sağ üstündeki <b>⋮</b> (üç nokta) menüsüne dokunun.</li><li><b>“Uygulamayı yükle”</b> veya <b>“Ana ekrana ekle”</b> seçeneğine dokunun.</li><li><b>Yükle / Ekle</b> deyin. Telefonun ana ekranında ServisPlus simgesi belirir.</li></ol>') +
      '<button type="button" style="margin-top:14px;width:100%;border:0;background:#2563eb;color:#fff;border-radius:12px;padding:12px;font-weight:700;font-size:15px">Tamam</button></div>';
    d.onclick = function (e) { if (e.target === d || e.target.tagName === 'BUTTON') d.remove(); };
    document.body.appendChild(d);
  }
  function pwaInstall() {
    var ev = PWA.ev;
    if (!ev || pwaIOS()) { pwaSteps(); return; }
    PWA.ev = null;
    try { ev.prompt(); ev.userChoice.then(function (r) { var o = pwaGet(); if (r && r.outcome === 'accepted') { o.installed = 1; pwaSet(o); toast('Uygulama yükleniyor… Ana ekranınızda ServisPlus simgesi görünecek'); } else { o.d = (o.d || 0) + 1; o.t = Date.now(); pwaSet(o); } var b = document.getElementById('spx-pwa'); if (b) b.remove(); var c = document.getElementById('spx-pwa-card'); if (c && r && r.outcome === 'accepted') c.remove(); }); } catch (e) { pwaSteps(); }
  }
  function pwaBar() {
    var ex = document.getElementById('spx-pwa'), o = pwaGet();
    var okCtx = document.body.classList.contains('spx-tech') && pwaAndroid() && !pwaStandalone() && !o.installed && !CNS.show && /^\/tech\/?$/.test(location.pathname);
    if (!okCtx) { if (ex) ex.remove(); return; }
    if (ex || PWA.shown) return;
    if ((o.d || 0) >= 2 || (o.t && Date.now() - o.t < 7 * 864e5)) return;      /* en fazla 2 kez; "Sonra"dan sonra 7 gun sessiz */
    if (!PWA.t0) { PWA.t0 = Date.now(); return; }
    if (Date.now() - PWA.t0 < 8000) return;                                     /* acilir acilmaz degil, birkac sn sonra */
    PWA.shown = true;
    var b = document.createElement('div'); b.id = 'spx-pwa'; b.className = 'notranslate';
    b.style.cssText = 'position:fixed;left:10px;right:10px;bottom:82px;z-index:9996;background:#fff;border:1px solid #cbd5e1;border-radius:14px;padding:10px 12px;display:flex;gap:10px;align-items:center;box-shadow:0 6px 20px rgba(15,23,42,.18)';
    b.innerHTML = '<img src="/icon-192.png" alt="" style="width:38px;height:38px;border-radius:9px;flex:none"><div style="flex:1;min-width:0"><div style="font-size:13.5px;font-weight:700;color:#0f172a">ServisPlus Usta uygulaması</div><div style="font-size:12px;color:#64748b">Ana ekrana ekleyin, tek dokunuşla açın.</div></div><button data-a="i" type="button" style="border:0;background:#2563eb;color:#fff;border-radius:10px;padding:9px 14px;font-weight:700;font-size:13.5px">İndir</button><button data-a="x" type="button" aria-label="Kapat" style="border:0;background:none;color:#94a3b8;font-size:20px;padding:2px 4px">×</button>';
    b.onclick = function (e) { var a = e.target.getAttribute && e.target.getAttribute('data-a'); if (!a) return; if (a === 'x') { var q = pwaGet(); q.d = (q.d || 0) + 1; q.t = Date.now(); pwaSet(q); b.remove(); } else { b.remove(); pwaInstall(); } };
    document.body.appendChild(b);
  }
  function pwaCard() {
    var ex = document.getElementById('spx-pwa-card'), o = pwaGet();
    var ok = document.body.classList.contains('spx-tech') && (pwaAndroid() || pwaIOS()) && !pwaStandalone() && !o.installed && location.pathname.replace(/\/$/, '') === '/tech/more';
    if (!ok) { if (ex) ex.remove(); return; }
    if (ex) return; var host = document.querySelector('[data-testid="tech-more"]'); if (!host) return;
    ex = document.createElement('div'); ex.id = 'spx-pwa-card'; ex.className = 'notranslate rounded-xl border bg-card p-4 shadow-none border-slate-200';
    ex.innerHTML = '<div style="display:flex;gap:12px;align-items:center"><img src="/icon-192.png" alt="" style="width:44px;height:44px;border-radius:10px;flex:none"><div style="flex:1"><div style="font-weight:700;font-size:14px">Usta uygulamasını telefona indir</div><div style="font-size:12px;color:#64748b;margin-top:2px">Ana ekranınıza ServisPlus simgesi eklenir.</div></div><button type="button" style="border:0;background:#2563eb;color:#fff;border-radius:10px;padding:9px 14px;font-weight:700;font-size:13.5px">' + (pwaIOS() ? 'Nasıl?' : 'İndir') + '</button></div>';
    ex.querySelector('button').onclick = pwaInstall;
    host.insertBefore(ex, host.firstChild);
  }
  setInterval(function () { pwaBar(); pwaCard(); }, 1500);


  // ---- GUNCELLEME 126: Usta egitimleri - acilir/kapanir liste, "Okudum" -> "Okundu", Daha sekmesinde kalan egitim sayisi
  var TRN = { left: null, t: 0, busy: false, open: false };
  function trLoad(force) {
    if (TRN.busy || (!force && TRN.left !== null && Date.now() - TRN.t < 45000)) return; TRN.busy = true;
    pcall('GET', '/training/modules').then(function (a) { TRN.left = (a || []).filter(function (m) { return m.active !== false && !m.done_at; }).length; TRN.t = Date.now(); }).catch(function () { TRN.t = Date.now(); }).then(function () { TRN.busy = false; });
  }
  function trStyle() {
    if (document.getElementById('spx-trcss')) return; var st = document.createElement('style'); st.id = 'spx-trcss';
    st.textContent = '.spx-mc>:not(:first-child){display:none}.spx-mc.spx-open>:not(:first-child){display:block}.spx-mc>:first-child{cursor:pointer}.spx-mc .spx-chv{display:inline-block;width:16px;transition:transform .15s;color:#64748b}.spx-mc.spx-open .spx-chv{transform:rotate(90deg)}.spx-trb{position:absolute;top:2px;left:calc(50% + 6px);min-width:18px;height:18px;border-radius:9px;background:#ef4444;color:#fff;font:700 11px/18px system-ui;text-align:center;padding:0 5px;pointer-events:none}.spx-trchip{margin-left:8px;background:#fee2e2;color:#b91c1c;border-radius:99px;padding:2px 9px;font-size:11.5px;font-weight:700}.spx-trchip.ok{background:#dcfce7;color:#166534}';
    document.head.appendChild(st);
  }
  function trUI() {
    if (!document.body.classList.contains('spx-tech') || !LS.get('token', '')) return;
    trStyle(); trLoad(false);
    var tab = document.querySelector('[data-testid="tab-more"]');
    if (tab) {
      if (getComputedStyle(tab).position === 'static') tab.style.position = 'relative';
      var bd = tab.querySelector('.spx-trb');
      if (TRN.left > 0) { if (!bd) { bd = document.createElement('span'); bd.className = 'spx-trb notranslate'; tab.appendChild(bd); } if (bd.textContent !== String(TRN.left)) bd.textContent = TRN.left; }
      else if (bd) bd.remove();
      if (!tab.getAttribute('data-spx-trk')) { tab.setAttribute('data-spx-trk', '1'); tab.addEventListener('click', function () { if (TRN.left > 0) TRN.open = true; }, true); }
    }
    var card = document.querySelector('[data-testid="training-card"]'); if (!card) return;
    card.style.display = 'none';
    var bt = document.getElementById('spx-trbtn');
    if (!bt) {
      bt = document.createElement('button'); bt.id = 'spx-trbtn'; bt.type = 'button'; bt.className = 'notranslate'; bt.style.cssText = 'display:flex;align-items:center;gap:12px;width:100%;text-align:left;background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:14px;font:inherit;cursor:pointer';
      bt.onclick = function () { trOpen(); }; card.parentNode.insertBefore(bt, card);
    }
    var lt = TRN.left, h = '<span style="font-size:24px">📚</span><span style="flex:1"><b style="font-size:15px;display:block">Eğitimler</b><span style="font-size:12.5px;color:#64748b">' + (lt === null ? 'Yükleniyor…' : lt > 0 ? lt + ' eğitim okunmayı bekliyor' : 'Tüm eğitimler tamamlandı ✔') + '</span></span>' + (lt > 0 ? '<span class="spx-trchip" style="margin:0">' + lt + '</span>' : '') + '<span style="color:#94a3b8;font-size:18px">›</span>';
    if (bt.getAttribute('data-h') !== h) { bt.setAttribute('data-h', h); bt.innerHTML = h; }
    if (TRN.open || location.hash === '#egitim') { TRN.open = false; try { history.replaceState(null, '', location.pathname); } catch (e) { } trOpen(); }
  }
  var TRM = null;
  function trOpen() {
    if (document.getElementById('spx-trov')) return;
    var ov = document.createElement('div'); ov.id = 'spx-trov'; ov.className = 'notranslate'; ov.style.cssText = 'position:fixed;inset:0;z-index:99997;background:#f1f5f9;display:flex;flex-direction:column';
    ov.innerHTML = '<div style="display:flex;gap:8px;align-items:center;padding:10px 12px;background:#fff;border-bottom:1px solid #e2e8f0"><button data-a="x" style="border:1px solid #cbd5e1;background:#fff;border-radius:10px;padding:9px 14px;font-weight:700;font-size:14px">← Geri</button><div style="flex:1;font-weight:800;font-size:15px;text-align:center">Eğitimler</div><span id="spx-trcnt" style="min-width:70px;text-align:right;font-size:12.5px;font-weight:700;color:#b91c1c"></span></div><div id="spx-trlist" style="flex:1;overflow:auto;padding:12px;-webkit-overflow-scrolling:touch"><div style="color:#64748b;padding:20px;text-align:center">Yükleniyor…</div></div>';
    document.body.appendChild(ov);
    var open = {};
    function paint() {
      var L = ov.querySelector('#spx-trlist'), list = TRM || [], left = list.filter(function (m) { return !m.done_at; }).length;
      ov.querySelector('#spx-trcnt').textContent = left ? left + ' kaldı' : 'Tamamlandı ✔'; ov.querySelector('#spx-trcnt').style.color = left ? '#b91c1c' : '#166534';
      L.innerHTML = list.length ? list.map(function (m) {
        var no = (/^\s*(\d+)\)/.exec(m.title) || [])[1], g = no && GUIDE[no] ? GUIDE[no] : null, o = !!open[m.id];
        var body = !o ? '' : '<div style="padding:4px 14px 14px"><div style="white-space:pre-wrap;font-size:13.5px;line-height:1.6;color:#334155">' + esc(m.content || '') + '</div>' + (m.url ? '<a href="' + esc(m.url) + '" target="_blank" rel="noopener" style="display:inline-block;margin-top:8px;color:#2563eb;font-weight:700;font-size:13.5px">Bağlantıyı aç ↗</a>' : '') +
          (g ? g.map(function (x) { return '<figure style="margin:14px 0 0"><img loading="lazy" src="/rehber/' + x[0] + '.jpg" alt="' + esc(x[1]) + '" style="width:100%;max-width:320px;display:block;margin:0 auto;border:1px solid #e2e8f0;border-radius:12px"><figcaption style="font-size:12.5px;color:#334155;margin-top:6px"><b>' + esc(x[1]) + '</b><ol style="margin:4px 0 0;padding:0;list-style:none">' + x[2].map(function (t, k) { return '<li style="display:flex;gap:7px;margin:2px 0"><span style="flex:none;min-width:18px;height:18px;border-radius:9px;background:#e11d48;color:#fff;font:700 11px/18px system-ui;text-align:center">' + (k + 1) + '</span><span>' + esc(t) + '</span></li>'; }).join('') + '</ol></figcaption></figure>'; }).join('') : '') +
          (m.done_at ? '' : '<button data-a="done" data-id="' + esc(m.id) + '" style="width:100%;margin-top:14px;border:0;background:#16a34a;color:#fff;border-radius:12px;padding:13px;font-weight:800;font-size:15px">Okudum</button>') + '</div>';
        return '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;margin-bottom:10px;overflow:hidden"><div data-a="tg" data-id="' + esc(m.id) + '" style="display:flex;align-items:center;gap:10px;padding:14px;cursor:pointer"><span style="color:#64748b;width:14px">' + (o ? '▾' : '▸') + '</span><b style="flex:1;font-size:14.5px;line-height:1.35">' + esc(m.title) + '</b>' + (m.done_at ? '<span style="color:#166534;font-size:12px;font-weight:700;white-space:nowrap">Okundu ✔</span>' : '<span style="color:#b91c1c;font-size:12px;font-weight:700;white-space:nowrap">Okunmadı</span>') + '</div>' + body + '</div>';
      }).join('') : '<div style="color:#64748b;padding:20px;text-align:center">Henüz eğitim eklenmemiş.</div>';
    }
    function load() { return pcall('GET', '/training/modules').then(function (a) { TRM = a || []; TRN.left = TRM.filter(function (m) { return m.active !== false && !m.done_at; }).length; TRN.t = Date.now(); var f = TRM.filter(function (m) { return !m.done_at; })[0]; if (f && !Object.keys(open).length) open[f.id] = 1; paint(); }).catch(function (e) { ov.querySelector('#spx-trlist').innerHTML = '<div style="color:#b91c1c;padding:20px">Eğitimler yüklenemedi</div>'; }); }
    ov.onclick = function (e) {
      var t = e.target.closest && e.target.closest('[data-a]'); if (!t) return; var a = t.getAttribute('data-a'), id = t.getAttribute('data-id');
      if (a === 'x') { ov.remove(); }
      else if (a === 'tg') { open[id] = !open[id]; paint(); }
      else if (a === 'done') { t.disabled = true; t.textContent = 'Kaydediliyor…'; call('POST', '/training/modules/' + encodeURIComponent(id) + '/complete').then(function () { var m = (TRM || []).filter(function (z) { return z.id === id; })[0]; if (m) m.done_at = new Date().toISOString(); open[id] = false; var nx = (TRM || []).filter(function (z) { return !z.done_at; })[0]; if (nx) open[nx.id] = true; TRN.left = (TRM || []).filter(function (z) { return z.active !== false && !z.done_at; }).length; paint(); toast('Okundu olarak işaretlendi ✔'); load(); }).catch(function (er) { t.disabled = false; t.textContent = 'Okudum'; fail(er); }); }
    };
    load();
  }
  setInterval(trUI, 800);

  /* ===== Usta egitim dokumanlarina ekran goruntuleri (nereden yapilacagi kirmizi kutu + numarayla gosterilir) ===== */
  var GUIDE = {"1": [["ana-ekran", "Görevler (ana ekran)", ["Puanım kartı", "Arıza Asistanı", "Sekmeler: Aktif Görevler / Tamamlanan / Atölye", "Görev kartı (dokununca iş detayı açılır)", "Alt menü: Görevler, Sohbet, Teklif, Duyuru, Bakiyem, Daha"]], ["ust-cubuk", "Üst çubuk", ["Bildirim zili (dokunup izin verin)", "Dil seçimi", "Çıkış", "Logo"]]], "2": [["is-atandi", "İş detayı – durum: Atandı", ["Yoldayım (müşteriye “usta yolda” mesajı + takip linki)", "Müşteriye mesaj", "Yola Çık (durumu Yolda yapar)", "Arıza Asistanı"]], ["is-yolda", "İş detayı – durum: Yolda", ["Servise Başla (müşteriye vardığınızda)"]]], "3": [["is-form-ust", "İş formu (durum: Başladı) – üst bölüm", ["Yapılan İş", "Sesle yaz", "AI ile düzelt", "Yedek Parçalar", "Ekle (stoktan seçin veya “Manuel”)"]], ["is-form-alt", "İş formu – alt bölüm", ["İşçilik (₺)", "Fotoğraflar", "Önce fotoğrafı", "Sonra fotoğrafı", "Kaydet", "Tamamla"]]], "4": [["is-form-en-alt", "İş detayı – sayfanın en altı", ["QR Etiket", "Atölyeye Al (yalnızca durum Başladı iken)", "Müşteri Vazgeçti"]]], "5": [["teklif", "Teklif sekmesi", ["Yeni: yeni fiyat teklifi oluşturur", "Fiyat Teklifi başlığı"]], ["sohbet", "Sohbet sekmesi", ["Merkez ile sohbet alanı", "Mesaj yazma kutusu", "Gönder"]]], "6": [["bakiyem", "Bakiyem sekmesi", ["Şirkete borç oranınız ve şirket IBAN bilgisi", "Ödeme yaptım (şirkete bildir)", "Bakiye durumu"]], ["profil", "Profilim (Daha → Profilim)", ["IBAN alanı", "Profili Kaydet", "Şifreyi Güncelle"]], ["daha-ust", "Daha sayfası – üst bölüm", ["Bugünkü rota", "Bu ayki karnem", "Eğitimler", "Okudum düğmesi"]]], "7": [["daha-alt", "Daha sayfası – alt bölüm", ["Arıza Rehberi", "Profilim", "Yazı boyutu (A− / A+)"]], ["daha-sss", "Daha → Sık Sorulan Sorular", ["Başlık", "Arama kutusu"]], ["indir-bar", "Android: uygulamayı indir önerisi (Görevler ekranında, nadiren çıkar)", ["İndir: ana ekrana ServisPlus simgesi ekler"]], ["daha-indir", "Daha → Usta uygulamasını telefona indir", ["İndir"]]]};
  function techGuideImgs() {
    var card = document.querySelector('[data-testid="training-card"]');
    if (!card || !document.body.classList.contains('spx-tech')) return;
    [].forEach.call(card.querySelectorAll('b.flex-1'), function (b) {
      var m = /^\s*(\d)\)\s/.exec(b.textContent || ''), row = b.closest('div.border-t') || (b.parentElement && b.parentElement.parentElement);
      if (!m || !row || row.getAttribute('data-spx-g') || !GUIDE[m[1]]) return;
      row.setAttribute('data-spx-g', '1');
      var box = document.createElement('div'); box.className = 'notranslate'; box.style.cssText = 'margin-top:10px';
      box.innerHTML = GUIDE[m[1]].map(function (g) {
        return '<figure style="margin:0 0 14px"><img loading="lazy" src="/rehber/' + g[0] + '.jpg" alt="' + esc(g[1]) + '" style="width:100%;max-width:320px;display:block;margin:0 auto;border:1px solid #e2e8f0;border-radius:12px;cursor:zoom-in">' +
          '<figcaption style="font-size:12.5px;color:#334155;margin-top:6px"><b>' + esc(g[1]) + '</b><ol style="margin:4px 0 0;padding:0;list-style:none">' +
          g[2].map(function (t, i) { return '<li style="display:flex;gap:7px;align-items:flex-start;margin:2px 0"><span style="flex:none;min-width:18px;height:18px;border-radius:9px;background:#e11d48;color:#fff;font:700 11px/18px system-ui;text-align:center">' + (i + 1) + '</span><span>' + esc(t) + '</span></li>'; }).join('') + '</ol></figcaption></figure>';
      }).join('');
      box.addEventListener('click', function (e) {
        var im = e.target.tagName === 'IMG' ? e.target : null; if (!im) return;
        var o = document.createElement('div'); o.style.cssText = 'position:fixed;inset:0;z-index:100001;background:rgba(15,23,42,.88);overflow:auto;padding:12px;display:flex;justify-content:center;cursor:zoom-out';
        o.innerHTML = '<img src="' + im.src + '" style="width:100%;max-width:520px;height:auto;align-self:flex-start;border-radius:10px">'; o.onclick = function () { o.remove(); }; document.body.appendChild(o);
      });
      row.appendChild(box);
    });
  }
  setInterval(techGuideImgs, 1200);


  /* ===== Giris ekraninda "Uye ol" (usta / servis is ortagi basvurusu: sitedeki mevcut form acilir) ===== */
  function loginSignup() {
    var ex = document.getElementById('spx-signup'), pw = document.querySelector('input[type="password"]');
    var onLogin = !!pw && !document.querySelector('[data-testid="settings-page"]') && (/login|giris/i.test(location.pathname) || /^\/?$/.test(location.pathname));
    if (!onLogin || document.body.classList.contains('spx-tech')) { if (ex) ex.remove(); return; }
    if (ex) return;
    var form = pw.closest('form'); if (!form) return;
    var btn = form.querySelector('button[type="submit"],button:not([type])'); if (!btn || !btn.parentElement) return;
    var cs = getComputedStyle(btn), host = location.hostname.replace(/^bayi\./, '');
    var url = /^(localhost|127\.)/.test(host) ? 'https://servisplus.net.tr/servisimiz-olun/' : 'https://' + host + '/servisimiz-olun/';
    var w = document.createElement('div'); w.id = 'spx-signup'; w.className = 'notranslate'; w.style.cssText = 'margin-top:14px;text-align:center';
    w.innerHTML = '<div style="font-size:13.5px;color:#64748b;margin-bottom:8px">Henüz hesabınız yok mu?</div>' +
      '<a href="' + url + '" target="_blank" rel="noopener" style="display:flex;align-items:center;justify-content:center;box-sizing:border-box;width:100%;min-height:' + Math.max(44, parseInt(cs.height, 10) || 44) + 'px;border:2px solid #2d5bd8;color:#2d5bd8;background:transparent;border-radius:' + (cs.borderRadius || '10px') + ';font-weight:700;font-size:' + (cs.fontSize || '16px') + ';text-decoration:none">Üye Ol – Usta / İş Ortağı Başvurusu</a>' +
      '<div style="font-size:12px;color:#94a3b8;margin-top:6px">Başvurunuz incelenir, onaylanınca giriş bilgileriniz size iletilir.</div>';
    btn.parentElement.insertBefore(w, btn.nextSibling);
  }
  setInterval(loginSignup, 1000);

})();

/* Admin mobil ust cubukta "ServisPlus" yazisi yerine logo (usta panelinde degil) */
(function () {
  function logoFix() {
    if (document.body.classList.contains('spx-tech')) return;
    var a = document.querySelector('header.lg\\:hidden a.font-display'); if (!a || a.getAttribute('data-logo')) return;
    if (!/ServisPlus/i.test(a.textContent)) return;
    a.setAttribute('data-logo', '1'); a.setAttribute('aria-label', 'ServisPlus');
    a.innerHTML = '<img src="/logo-servisplus.jpg" alt="ServisPlus" style="height:36px;width:auto;display:block;mix-blend-mode:multiply">';
  }
  setInterval(logoFix, 500);
})();

/* Mobil: genis tablolar yan kaydirma yerine kart gorunumunde (<=768px). Masaustu degismez. */
(function () {
  var s = document.createElement('style');
  s.textContent = '@media(max-width:768px){' +
    'main table.spx-card{display:block;width:100%;min-width:0!important;padding:0!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important}main table.spx-card td span,main table.spx-card td .rounded-full{white-space:nowrap}main table.spx-card td button,main table.spx-card td a{padding:2px 6px!important;min-height:28px!important}' +
    'main table.spx-card thead{display:none}' +
    'main table.spx-card tbody{display:block}' +
    'main table.spx-card tr{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:5px 10px;border:1px solid #e2e8f0;border-radius:0;margin:0 0 6px;padding:7px 10px;background:#fff}' +
    'main table.spx-card td{display:block;min-width:0;padding:0!important;border:0!important;text-align:left;white-space:normal;word-break:break-word;font-size:13.5px;line-height:1.3}' +
    'main table.spx-card td::before{content:attr(data-label);display:block;font-size:9.5px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:#94a3b8;margin-bottom:1px}' +
    'main table.spx-card td[data-label=""]::before,main table.spx-card td:not([data-label])::before{display:none}' +
    'main table.spx-card td:empty{display:none}' +
    'main table.spx-card td{grid-column:span 3}main table.spx-card td.spx-s{grid-column:span 2}main table.spx-card td.spx-first{grid-column:1/-1;display:flex;align-items:center;gap:10px;border-bottom:1px solid #f1f5f9!important;padding-bottom:6px!important}' +
    'main table.spx-card td.spx-first::before{display:none}' +
    'main table.spx-card td.spx-last{grid-column:1/-1;display:flex;justify-content:flex-end;align-items:center;gap:14px;flex-wrap:wrap;padding-top:0!important;margin-top:-2px}' +
    'main table.spx-card td.spx-last::before{display:none}' +
    'main table.spx-card td > *{max-width:100%}' +
    '.spx-wrap0{border-radius:0!important;padding:0!important;border:0!important;background:transparent!important;box-shadow:none!important}.spx-wrap0>*{padding-left:0!important;padding-right:0!important}' +
    '[data-testid^="tech-card-"]{padding:12px!important}[data-testid^="tech-card-"] .mt-4.grid{margin-top:8px!important;gap:6px!important}[data-testid^="tech-card-"] .mt-4.grid>div{padding:4px 6px!important}[data-testid^="tech-card-"] .mt-4.grid .font-display{font-size:15px!important;line-height:20px!important}[data-testid^="tech-card-"] .mt-4.text-xs{margin-top:6px!important}[data-testid^="tech-card-"] .mt-3.flex{margin-top:8px!important}' +
    '.spx-tp>div:last-child{display:flex!important;flex-wrap:wrap;gap:6px!important}.spx-tp>div:last-child>button{width:auto!important;margin:0!important;padding:5px 10px!important;font-size:12px!important}' +
    '}';
  document.head.appendChild(s);
  function cardify() {
    if (innerWidth > 768) return;
    Array.prototype.forEach.call(document.querySelectorAll('main table'), function (t) {
      var ths = t.querySelectorAll('thead th'); if (!ths.length) return;
      t.classList.add('spx-card');
      var w0 = t.closest('.rounded-xl'); if (w0 && w0.tagName === 'DIV' && !w0.classList.contains('spx-wrap0') && w0.contains(t) && w0.querySelectorAll('table').length === 1) w0.classList.add('spx-wrap0');
      var lab = Array.prototype.map.call(ths, function (h) { return (h.textContent || '').trim(); });
      Array.prototype.forEach.call(t.querySelectorAll('tbody tr'), function (tr) {
        var tds = tr.children; if (tds.length !== lab.length) return;
        for (var i = 0; i < tds.length; i++) {
          if (tds[i].getAttribute('data-label') !== lab[i]) tds[i].setAttribute('data-label', lab[i]);
          var f = i === 0, l = i === tds.length - 1 && (!lab[i] || /^(İşlem|Islem|İşlemler)$/i.test(lab[i])), sh = !f && !l && (tds[i].textContent || '').trim().length <= 13;
          if (tds[i].classList.contains('spx-s') !== sh) tds[i].classList.toggle('spx-s', sh);
          if (tds[i].classList.contains('spx-first') !== f) tds[i].classList.toggle('spx-first', f);
          if (tds[i].classList.contains('spx-last') !== l) tds[i].classList.toggle('spx-last', l);
        }
      });
    });
  }
  setInterval(cardify, 700);
})();

/* Mobil: tasan buton satirlarini alt satira sar, kucuk dokunma alanlarini buyut */
(function () {
  var s = document.createElement('style');
  s.textContent = '@media(max-width:768px){main table.spx-card td a,main table.spx-card td button{min-height:30px;display:inline-flex;align-items:center}main table.spx-card td a{padding:4px 2px}}';
  document.head.appendChild(s);
  function wrapRows() {
    if (innerWidth > 768) return;
    Array.prototype.forEach.call(document.querySelectorAll('main div.flex'), function (d) {
      if (d.style.flexWrap === 'wrap' || d.closest('table,.overflow-x-auto')) return;
      if (d.scrollWidth > d.clientWidth + 2 || d.getBoundingClientRect().right > innerWidth + 2) d.style.flexWrap = 'wrap';
    });
  }
  setInterval(wrapRows, 900);

  // ---- GUNCELLEME 170: profil fotograflari (admin/usta is detayinda musteri + usta; admin usta kartlarinda usta)
  function pfaTok() { try { return localStorage.getItem('token') || ''; } catch (e) { return ''; } }
  function pfaEsc(x) { return String(x == null ? '' : x).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function pfaCall(m, p, b) { var o = { method: m, headers: { Authorization: 'Bearer ' + pfaTok() } }; if (b) { o.headers['Content-Type'] = 'application/json'; o.body = JSON.stringify(b); } return fetch(location.origin + '/api' + p, o).then(function (r) { return r.json().then(function (j) { if (!r.ok) throw new Error((j && typeof j.detail === 'string' && j.detail) || 'hata'); return j; }); }); }
  function pfaUrl(u) { return u && u.photo_path ? location.origin + '/api/files/' + u.photo_path + '?auth=' + encodeURIComponent(pfaTok()) + '&v=' + encodeURIComponent(u.photo_at || '') : ''; }
  var PFA = { id: '', d: null, t: 0, busy: false, techs: null, tt: 0, tb: false };
  function pfaCircle(src, nm, sz) {
    var ini = String(nm || '?').trim().split(/\s+/).slice(0, 2).map(function (x) { return x.charAt(0).toUpperCase(); }).join('');
    return '<span style="width:' + sz + 'px;height:' + sz + 'px;border-radius:50%;background:#0a1f44;color:#fff;overflow:hidden;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:' + Math.round(sz / 2.6) + 'px;flex:none;border:2px solid #e2e8f0">' + (src ? '<img alt="" src="' + src + '" style="width:100%;height:100%;object-fit:cover;display:block">' : pfaEsc(ini)) + '</span>';
  }
  function pfaJob() {
    var tm = location.pathname.match(/^\/tech\/jobs\/([^/]+)/), am = location.pathname.match(/^\/admin\/jobs\/([^/]+)/), ex = document.getElementById('spx-pf');
    var tech = document.body.classList.contains('spx-tech');
    var host = tm && tech ? document.querySelector('[data-testid="tech-job-detail"]') : (am && !tech ? (function () { var h = document.querySelector('[data-testid="status-select"]'); return h && h.closest('.rounded-xl'); })() : null);
    var id = tm ? tm[1] : am ? am[1] : '';
    if (!host || !id || !pfaTok()) { if (ex) ex.remove(); return; }
    if (PFA.id !== id) { PFA.id = id; PFA.d = null; PFA.t = 0; if (ex) ex.remove(); ex = null; }
    if ((!PFA.d || Date.now() - PFA.t > 60000) && !PFA.busy) { PFA.busy = true; pfaCall('GET', '/avatar/job/' + id).then(function (d) { PFA.d = d; PFA.t = Date.now(); }).catch(function () { PFA.d = PFA.d || {}; PFA.t = Date.now(); }).then(function () { PFA.busy = false; }); }
    var d = PFA.d; if (!d || (!d.customer && !d.tech)) { if (ex) ex.remove(); return; }
    var h = (d.customer ? '<div style="display:flex;align-items:center;gap:10px">' + pfaCircle(d.customer, d.customer_name, 56) + '<div><div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:#64748b;font-weight:700">Müşteri</div><b>' + pfaEsc(d.customer_name || '') + '</b></div></div>' : '') +
      (d.tech ? '<div style="display:flex;align-items:center;gap:10px">' + pfaCircle(d.tech, d.tech_name, 56) + '<div><div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:#64748b;font-weight:700">Usta</div><b>' + pfaEsc(d.tech_name || '') + '</b></div></div>' : '');
    if (!ex) { ex = document.createElement('div'); ex.id = 'spx-pf'; ex.className = 'notranslate'; ex.style.cssText = 'border:1px solid #e2e8f0;border-radius:12px;padding:10px 13px;margin-bottom:12px;font-size:14px;display:flex;gap:22px;flex-wrap:wrap;align-items:center;background:#fff'; host.insertBefore(ex, host.firstChild); }
    else if (ex.parentNode !== host) host.insertBefore(ex, host.firstChild);
    if (ex.getAttribute('data-h') !== h) { ex.setAttribute('data-h', h); ex.innerHTML = h; }
  }
  function pfaTechCards() {
    var pg = document.querySelector('[data-testid="technicians-page"]'); if (!pg || document.body.classList.contains('spx-tech') || !pfaTok()) return;
    var cards = pg.querySelectorAll('[data-testid^="tech-card-"]'); if (!cards.length) return;
    if ((!PFA.techs || Date.now() - PFA.tt > 60000) && !PFA.tb) { PFA.tb = true; pfaCall('GET', '/technicians').then(function (a) { var m = {}; (a || []).forEach(function (u) { if (u.photo_path) m[u.id] = u; }); PFA.techs = m; PFA.tt = Date.now(); }).catch(function () { PFA.techs = PFA.techs || {}; PFA.tt = Date.now(); }).then(function () { PFA.tb = false; }); }
    if (!PFA.techs) return;
    Array.prototype.forEach.call(cards, function (c) {
      var id = (c.getAttribute('data-testid') || '').replace('tech-card-', ''), u = PFA.techs[id], ex = c.querySelector('.spx-tav');
      if (!u) { if (ex) ex.remove(); return; }
      var src = pfaUrl(u);
      if (ex && ex.getAttribute('data-s') === src) return;
      if (ex) ex.remove();
      if (getComputedStyle(c).position === 'static') c.style.position = 'relative';
      ex = document.createElement('div'); ex.className = 'spx-tav notranslate'; ex.setAttribute('data-s', src); ex.style.cssText = 'position:absolute;right:12px;bottom:12px;pointer-events:none';
      ex.innerHTML = pfaCircle(src, u.name, 40); c.appendChild(ex);
    });
  }
  setInterval(function () { try { pfaJob(); pfaTechCards(); } catch (e) { if (!window.__pfaW) { window.__pfaW = 1; console.warn('pfa', e && e.message); } } }, 900);

  // ---- GUNCELLEME 171: foto onayi + bakim zamani gelenler (admin)
  var PX = { fj: null, fid: '', ft: 0, fb: false, bk: null, bt: 0, bb: false, open: false, bq: null, bqt: 0, bqb: false };
  function pxToast(t) { var d = document.createElement('div'); d.textContent = t; d.style.cssText = 'position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#0a1f44;color:#fff;padding:11px 18px;z-index:99999;font-size:14px;max-width:90vw'; document.body.appendChild(d); setTimeout(function () { d.remove(); }, 3500); }
  var PXB = 'border:1px solid #cbd5e1;background:#fff;color:#0f172a;padding:5px 10px;font:inherit;font-size:12.5px;cursor:pointer;margin-left:4px';
  var PXO = 'border:1px solid #0a1f44;background:#0a1f44;color:#fff;padding:5px 10px;font:inherit;font-size:12.5px;cursor:pointer;margin-left:4px';
  function pxHost(id, host, html, first) {
    var ex = document.getElementById(id);
    if (!ex) { ex = document.createElement('div'); ex.id = id; ex.className = 'notranslate'; ex.style.cssText = 'border:1px solid #e2e8f0;border-radius:12px;padding:11px 13px;margin-bottom:14px;font-size:14px;background:#fff'; first ? host.insertBefore(ex, host.firstChild) : host.appendChild(ex); }
    else if (ex.parentNode !== host) { first ? host.insertBefore(ex, host.firstChild) : host.appendChild(ex); }
    if (ex.getAttribute('data-h') !== html) { ex.setAttribute('data-h', html); ex.innerHTML = html; }
    return ex;
  }
  // --- A) is detayi: musteriye gorunen fotograflar
  function pxJobFoto() {
    var am = location.pathname.match(/^\/admin\/jobs\/([^/]+)/), ex = document.getElementById('spx-fj');
    var h = document.querySelector('[data-testid="status-select"]'); h = h && h.closest('.rounded-xl');
    if (!am || !h || document.body.classList.contains('spx-tech') || !pfaTok()) { if (ex) ex.remove(); return; }
    var id = am[1]; if (PX.fid !== id) { PX.fid = id; PX.fj = null; PX.ft = 0; if (ex) ex.remove(); ex = null; }
    if ((!PX.fj || Date.now() - PX.ft > 30000) && !PX.fb) { PX.fb = true; pfaCall('GET', '/foto/job/' + id).then(function (d) { PX.fj = d; PX.ft = Date.now(); }).catch(function () { PX.fj = PX.fj || { items: [] }; PX.ft = Date.now(); }).then(function () { PX.fb = false; }); }
    var d = PX.fj; if (!d || !d.items.length) { if (ex) ex.remove(); return; }
    var L = { ok: ['#166534', '✔ Müşteriye görünür (onaylandı)'], gorunur: ['#166534', '✔ Müşteriye görünür'], hide: ['#b91c1c', '✖ Gizli'], bekliyor: ['#b45309', d.manual ? '⏳ Onayınızı bekliyor' : '⏳ ' + d.delay_min + ' dk sonra görünür'] };
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-bottom:8px"><b>📷 Müşteriye görünen fotoğraflar</b><span><button data-fa="ok-all" style="' + PXO + '">Tümünü onayla</button><button data-fa="hide-all" style="' + PXB + '">Tümünü gizle</button></span></div>' +
      '<div style="font-size:12px;color:#64748b;margin-bottom:8px">' + (d.done ? 'İş tamamlandı. ' : 'Fotoğraflar iş tamamlanınca müşteriye açılır. ') + 'Uygunsuz bir fotoğrafı gizleyin; müşteri takip sayfasında yalnızca görünür olanları görür.</div><div style="display:flex;gap:10px;flex-wrap:wrap">' +
      d.items.map(function (it) {
        var c = L[it.state] || L.bekliyor, u = location.origin + it.url + '?auth=' + encodeURIComponent(pfaTok());
        return '<div style="width:96px"><a href="' + u + '" target="_blank" rel="noreferrer"><img src="' + u + '" alt="" style="width:96px;height:96px;object-fit:cover;border:1px solid #e2e8f0;display:block"></a><div style="font-size:11px;font-weight:700;color:#64748b;margin-top:3px">' + (it.kind === 'before' ? 'ÖNCE' : 'SONRA') + '</div><div style="font-size:11.5px;color:' + c[0] + ';font-weight:600;min-height:28px">' + c[1] + '</div>' +
          '<button data-fa="ok" data-k="' + it.kind + '" data-i="' + it.i + '" style="' + PXO + ';margin:0 3px 0 0">Onayla</button><button data-fa="hide" data-k="' + it.kind + '" data-i="' + it.i + '" style="' + PXB + ';margin:0">Gizle</button></div>';
      }).join('') + '</div>';
    ex = pxHost('spx-fj', h, html, true);
    if (!ex.getAttribute('data-b')) { ex.setAttribute('data-b', '1'); ex.addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('[data-fa]'); if (!b) return; var a = b.getAttribute('data-fa'), body;
      if (a === 'ok-all') body = { kind: 'all', state: 'ok' }; else if (a === 'hide-all') body = { kind: 'all', state: 'hide' }; else body = { kind: b.getAttribute('data-k'), i: +b.getAttribute('data-i'), state: a };
      b.disabled = true; pfaCall('PUT', '/foto/job/' + PX.fid, body).then(function () { PX.ft = 0; pxToast('Kaydedildi'); }).catch(function (x) { pxToast(x.message); b.disabled = false; });
    }); }
  }
  // --- B) teknisyenler sayfasi: foto onay kutusu
  function pxFotoQueue() {
    var pg = document.querySelector('[data-testid="technicians-page"]'), ex = document.getElementById('spx-fq');
    if (!pg || document.body.classList.contains('spx-tech') || !pfaTok() || !/^\/admin\/technicians\/?$/.test(location.pathname)) { if (ex) ex.remove(); return; }
    if ((!PX.bq || Date.now() - PX.bqt > 20000) && !PX.bqb) { PX.bqb = true; pfaCall('GET', '/foto/bekleyen').then(function (d) { PX.bq = d; PX.bqt = Date.now(); }).catch(function () { PX.bqt = Date.now(); }).then(function () { PX.bqb = false; }); }
    var d = PX.bq; if (!d) return;
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap"><b>📷 Fotoğraf onayı</b><span style="font-size:12.5px;color:#475569">İş fotoğrafları: <b>' + (d.manual ? 'yalnızca onayladıklarınız' : 'iş bitince ' + d.delay_min + ' dk sonra otomatik') + '</b> görünür <button data-fq="mode" style="' + PXB + '">' + (d.manual ? 'Otomatiğe al' : 'Elle onaya al') + '</button><button data-fq="delay" style="' + PXB + '">Süre</button></span></div>';
    if (d.ustalar.length) {
      html += '<div style="margin-top:10px;font-size:12px;font-weight:700;color:#b45309;text-transform:uppercase;letter-spacing:.04em">Onay bekleyen usta profil fotoğrafları (' + d.ustalar.length + ')</div><div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:6px">' +
        d.ustalar.map(function (u) { var src = location.origin + '/api/files/' + u.photo_path + '?auth=' + encodeURIComponent(pfaTok()) + '&v=' + encodeURIComponent(u.photo_at || '');
          return '<div style="width:120px;text-align:center"><a href="' + src + '" target="_blank" rel="noreferrer"><img src="' + src + '" alt="" style="width:96px;height:96px;object-fit:cover;border-radius:50%;border:2px solid #e2e8f0"></a><div style="font-size:12.5px;font-weight:600;margin:3px 0">' + pfaEsc(u.name) + '</div><button data-fq="uok" data-id="' + u.id + '" style="' + PXO + ';margin:0 2px 0 0">Onayla</button><button data-fq="ured" data-id="' + u.id + '" style="' + PXB + ';margin:0">Reddet</button></div>'; }).join('') + '</div>';
    }
    if (d.isler.length) {
      html += '<div style="margin-top:10px;font-size:12px;font-weight:700;color:#b45309;text-transform:uppercase;letter-spacing:.04em">Onay/gözden geçirme bekleyen iş fotoğrafları (' + d.isler.length + ' iş)</div><div style="margin-top:4px">' +
        d.isler.slice(0, 8).map(function (j) { return '<a href="/admin/jobs/' + j.job_id + '" style="display:block;padding:4px 0;color:#1155cc;font-size:13px">' + pfaEsc(j.job_number) + ' · ' + pfaEsc(j.customer) + ' · ' + pfaEsc(j.tech || '') + ' <span style="color:#64748b">(' + j.count + ' fotoğraf)</span></a>'; }).join('') + (d.isler.length > 8 ? '<div style="font-size:12px;color:#64748b">… ve ' + (d.isler.length - 8) + ' iş daha</div>' : '') + '</div>';
    }
    ex = pxHost('spx-fq', pg, html, true);
    if (!ex.getAttribute('data-b')) { ex.setAttribute('data-b', '1'); ex.addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('[data-fq]'); if (!b) return; var a = b.getAttribute('data-fq'), p;
      if (a === 'mode') p = pfaCall('PUT', '/foto/ayar', { manual: !PX.bq.manual }); else if (a === 'delay') { var v = prompt('Fotoğraflar iş bittikten kaç dakika sonra müşteriye görünsün? (0–1440)', PX.bq.delay_min); if (v === null) return; p = pfaCall('PUT', '/foto/ayar', { delay_min: v }); }
      else if (a === 'uok') p = pfaCall('POST', '/foto/usta/' + b.getAttribute('data-id'), { state: 'ok' }); else if (a === 'ured') { if (!confirm('Fotoğraf reddedilsin ve kaldırılsın mı? Usta yenisini yükleyebilir.')) return; p = pfaCall('POST', '/foto/usta/' + b.getAttribute('data-id'), { state: 'red' }); } else return;
      b.disabled = true; p.then(function () { PX.bqt = 0; PF_TECHS_RESET(); pxToast('Kaydedildi'); }).catch(function (x) { pxToast(x.message); b.disabled = false; });
    }); }
  }
  function PF_TECHS_RESET() { try { PFA.tt = 0; } catch (e) {} }
  // --- C) servis kayitlari: bakim zamani gelenler
  function pxBakim() {
    var pg = document.querySelector('[data-testid="jobs-page"]'), ex = document.getElementById('spx-bkm');
    if (!pg || document.body.classList.contains('spx-tech') || !pfaTok() || !/^\/admin\/jobs\/?$/.test(location.pathname)) { if (ex) ex.remove(); return; }
    if ((!PX.bk || Date.now() - PX.bt > 60000) && !PX.bb) { PX.bb = true; pfaCall('GET', '/maintenance/due?ahead=30').then(function (d) { PX.bk = d; PX.bt = Date.now(); }).catch(function () { PX.bk = PX.bk || { items: [], months: 12 }; PX.bt = Date.now(); }).then(function () { PX.bb = false; }); }
    var d = PX.bk; if (!d) return; var it = d.items || [];
    if (!it.length) { if (ex) ex.remove(); return; }
    var todo = it.filter(function (x) { return !x.reminded_at && !x.requested; }).length;
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;cursor:pointer" data-bkm="toggle"><b>🔧 Bakım zamanı gelenler <span style="background:#f27a1a;color:#fff;padding:1px 8px;font-size:12px">' + it.length + '</span></b><span style="font-size:12.5px;color:#64748b">Kombi/klima · son servisten ' + d.months + ' ay · ' + (PX.open ? 'gizle ▲' : 'göster ▼') + '</span></div>';
    if (PX.open) {
      html += '<div style="margin:8px 0;font-size:12.5px;color:#64748b">Müşteriye giden mesajdaki bağlantıya dokunan müşterinin servis kaydı otomatik açılır. ' + (todo ? '<button data-bkm="all" style="' + PXO + '">Hatırlatılmamış ' + todo + ' kişiye hatırlat</button>' : '') + '</div><div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:13px"><thead><tr style="text-align:left;color:#64748b;font-size:11.5px;text-transform:uppercase"><th style="padding:4px 6px">Müşteri</th><th>Cihaz</th><th>Son servis</th><th>Durum</th><th></th></tr></thead><tbody>' +
        it.map(function (x) {
          var st = x.requested ? '<span style="color:#166534;font-weight:600">✔ Servis kaydı açıldı</span>' : x.reminded_at ? '<span style="color:#1e3a8a">Hatırlatıldı ' + pfaEsc(String(x.reminded_at).slice(0, 10)) + '</span>' : (x.overdue_days > 0 ? '<span style="color:#b91c1c;font-weight:600">' + x.overdue_days + ' gün gecikti</span>' : '<span style="color:#b45309">Yaklaşıyor · ' + pfaEsc(x.due) + '</span>');
          return '<tr style="border-top:1px solid #e2e8f0"><td style="padding:6px"><b>' + pfaEsc(x.name) + '</b><div style="color:#64748b;font-size:12px">' + pfaEsc(x.phone) + (x.district ? ' · ' + pfaEsc(x.district) : '') + '</div></td><td>' + pfaEsc(x.device) + '</td><td>' + pfaEsc(x.last) + '</td><td>' + st + '</td><td style="white-space:nowrap;text-align:right">' +
            (x.requested ? '' : '<button data-bkm="rem" data-key="' + x.key + '" style="' + PXB + '">' + (x.reminded_at ? 'Tekrar hatırlat' : 'Hatırlat') + '</button><button data-bkm="job" data-key="' + x.key + '" style="' + PXO + '">Servis kaydı oluştur</button><button data-bkm="skip" data-key="' + x.key + '" style="' + PXB + '" title="Cihazı satmış / istemiyor">Gerekmiyor</button>') + '</td></tr>'; }).join('') + '</tbody></table></div>';
    }
    ex = pxHost('spx-bkm', pg, html, true);
    if (!ex.getAttribute('data-b')) { ex.setAttribute('data-b', '1'); ex.addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('[data-bkm]'); if (!b) return; var a = b.getAttribute('data-bkm'), k = b.getAttribute('data-key');
      if (a === 'toggle') { PX.open = !PX.open; PX.bt = PX.bt; var x0 = document.getElementById('spx-bkm'); if (x0) x0.removeAttribute('data-h'); return; }
      var p;
      if (a === 'rem' || a === 'all') {
        var keys = a === 'all' ? PX.bk.items.filter(function (x) { return !x.reminded_at && !x.requested; }).map(function (x) { return x.key; }) : [k];
        if (a === 'all' && !confirm(keys.length + ' müşteriye bakım hatırlatma mesajı gönderilsin mi?')) return;
        p = pfaCall('POST', '/maintenance/remind', { keys: keys }).then(function (r) { PX.bt = 0;
          if (r.failed && !r.sent) { var l = Object.keys(r.links || {}).map(function (q) { return r.links[q]; })[0]; if (l && navigator.clipboard) { try { navigator.clipboard.writeText(l); } catch (z) {} } pxToast('Mesaj gönderilemedi (bildirim/SMS ayarını kontrol edin). Bağlantı kopyalandı: elle gönderebilirsiniz.'); }
          else pxToast(r.sent + ' mesaj gönderildi' + (r.failed ? ', ' + r.failed + ' gönderilemedi' : '')); });
      } else if (a === 'job') { if (!confirm('Bu müşteri için yıllık bakım servis kaydı oluşturulsun mu?')) return; p = pfaCall('POST', '/maintenance/create-job', { key: k }).then(function (r) { PX.bt = 0; pxToast('Servis kaydı açıldı: ' + (r.job_number || '')); if (r.job_id) { history.pushState({}, '', '/admin/jobs/' + r.job_id); window.dispatchEvent(new PopStateEvent('popstate')); } }); }
      else if (a === 'skip') { if (!confirm('Bu müşteri bir daha bakım listesinde çıkmasın mı?')) return; p = pfaCall('POST', '/maintenance/skip', { key: k }).then(function () { PX.bt = 0; pxToast('Listeden çıkarıldı'); }); } else return;
      b.disabled = true; p.catch(function (x) { pxToast(x.message); }).then(function () { b.disabled = false; });
    }); }
  }

  var PXN = { t: 0, b: false };
  function pxOnayBadge() {
    if (document.body.classList.contains('spx-tech') || !pfaTok() || !document.querySelector('[data-spx-own]')) return;
    if (Date.now() - PXN.t > 45000 && !PXN.b) { PXN.b = true; pfaCall('GET', '/foto/sayi').then(function (r) { window.__onayN = r.n || 0; }).catch(function () { }).then(function () { PXN.t = Date.now(); PXN.b = false; }); }
    var a = document.querySelector('[data-spx-own] a.spx-it[data-k="ek:onay"]'); if (!a) return; var bd = a.querySelector('.spx-bd:not(.spx-od)'), t = window.__onayN ? String(window.__onayN) : '';
    if (t) { if (!bd) { bd = document.createElement('span'); bd.className = 'spx-bd'; a.appendChild(bd); } if (bd.textContent !== t) bd.textContent = t; } else if (bd) bd.remove();
  }
  setInterval(function () { try { pxJobFoto(); pxBakim(); pxOnayBadge(); } catch (e) { if (!window.__pxW) { window.__pxW = 1; console.warn('px', e && e.message); } } }, 1000);
})();

/* ---------- G178: Genel Bakış "Bugün" şeridi + mobil hızlı işlem (+) butonu ---------- */
(function () {
  if (window.__spxBugun) return; window.__spxBugun = 1;
  var API = (window.SP_PANEL_API || location.origin + '/api');
  function tok() { try { return localStorage.getItem('token') || ''; } catch (e) { return ''; } }
  function isAdm() { return /^\/admin(\/|$)/.test(location.pathname) && !document.body.classList.contains('spx-tech') && !!tok(); }
  function go(w) {
    if (w.indexOf('ek:') === 0) { if (window.spxOpen) window.spxOpen(w.slice(3)); return; }
    var ov = document.getElementById('spx-ov'); if (ov) ov.classList.remove('on');
    try { history.pushState({}, '', w); window.dispatchEvent(new PopStateEvent('popstate', { state: {} })); } catch (e) { location.href = w; }
  }
  function jobs(scope) { var JF = window.SPX_JF; if (JF) { JF.q = ''; JF.scope = scope; try { localStorage.setItem('spx_jf', JSON.stringify(JF)); } catch (e) { } } go('/admin/jobs'); }
  function tl(n) { try { return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(n || 0); } catch (e) { return Math.round(n || 0) + ' ₺'; } }
  var st = document.createElement('style');
  st.textContent = '#spx-bugun{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:0 0 16px}' +
    '#spx-bugun .bg{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:12px 14px;cursor:pointer;text-align:left;font:inherit;color:#0f172a;transition:transform .12s,box-shadow .12s;position:relative;overflow:hidden}' +
    '#spx-bugun .bg:hover{transform:translateY(-1px);box-shadow:0 6px 16px -8px rgba(15,23,42,.25)}#spx-bugun .bg:before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--c)}' +
    '#spx-bugun .bg small{display:block;font-size:11.5px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.03em}#spx-bugun .bg b{display:block;font-size:24px;font-weight:800;margin-top:4px;line-height:1.1}#spx-bugun .bg i{display:block;font-style:normal;font-size:12px;color:#64748b;margin-top:3px}' +
    '#spx-bugun .bg.al b{color:var(--c)}#spx-bugun .hd{grid-column:1/-1;display:flex;justify-content:space-between;align-items:baseline;font-weight:800;font-size:15px;color:#0f172a}#spx-bugun .hd span{font-weight:600;font-size:12px;color:#64748b}' +
    'html.spx-dark #spx-bugun .bg{background:#111a2e;border-color:#1f2d47;color:#e2e8f0}html.spx-dark #spx-bugun .hd{color:#e2e8f0}' +
    '@media(max-width:640px){#spx-bugun{grid-template-columns:repeat(2,1fr);gap:8px}#spx-bugun .bg{padding:10px 12px}#spx-bugun .bg b{font-size:20px}}' +
    '#spx-fab{position:fixed;right:16px;bottom:88px;z-index:60;width:56px;height:56px;border-radius:50%;border:0;background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;box-shadow:0 10px 24px -6px rgba(37,99,235,.6);display:none;align-items:center;justify-content:center;cursor:pointer;transition:transform .15s}' +
    '#spx-fab svg{width:26px;height:26px;transition:transform .2s}#spx-fab.on svg{transform:rotate(45deg)}' +
    '#spx-fabm{position:fixed;right:16px;bottom:154px;z-index:61;display:none;flex-direction:column;gap:8px;align-items:flex-end}#spx-fabm.on{display:flex}' +
    '#spx-fabm button{display:flex;align-items:center;gap:10px;border:0;background:#fff;color:#0f172a;border-radius:14px;padding:11px 14px;font:700 14px/1 Inter,system-ui,sans-serif;box-shadow:0 8px 20px -6px rgba(15,23,42,.35);cursor:pointer}' +
    '#spx-fabm button i{width:30px;height:30px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-style:normal;color:#fff;font-size:16px}' +
    '#spx-fabbg{position:fixed;inset:0;z-index:59;background:rgba(15,23,42,.35);display:none}#spx-fabbg.on{display:block}' +
    'html.spx-dark #spx-fabm button{background:#111a2e;color:#e2e8f0}' +
    'html.spx-dark [data-testid="dashboard-summary"]{background:#111a2e!important;border-color:#1f2d47!important;color:#e2e8f0}html.spx-dark [data-testid="dashboard-summary"] *{color:inherit}html.spx-dark [data-testid="dashboard-summary"] [class*="rounded-full"]{background:#1d2a42!important;border-color:#2b3b5c!important}' +
    '@media(max-width:1023px){body.spx-fabok #spx-fab{display:flex}}';
  document.head.appendChild(st);

  /* --- Bugün şeridi --- */
  var BG = { d: null, t: 0, busy: false };
  function load() {
    if (BG.busy || Date.now() - BG.t < 60000) return; BG.busy = true;
    fetch(API + '/admin/bugun', { headers: { Authorization: 'Bearer ' + tok() } }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d) { BG.d = d; render(); } }).catch(function () { }).then(function () { BG.t = Date.now(); BG.busy = false; });
  }
  function tile(lbl, val, sub, c, act, alert) { return '<button class="bg' + (alert ? ' al' : '') + '" style="--c:' + c + '" data-bg="' + act + '"><small>' + lbl + '</small><b>' + val + '</b><i>' + sub + '</i></button>'; }
  function render() {
    var box = document.getElementById('spx-bugun'), d = BG.d; if (!box || !d) return;
    var h = '<div class="hd">Bugün <span>Dokunun, ilgili listeye gider · 1 dk\'da bir yenilenir</span></div>' +
      tile('Bugün açılan kayıt', d.created_today, d.scheduled_today + ' iş bugüne planlı', '#2563eb', 'today') +
      tile('Atanmamış', d.unassigned, 'Usta bekleyen iş', '#d97706', 'jobs', d.unassigned > 0) +
      tile('Geciken', d.overdue, 'Randevu saati geçmiş', '#dc2626', 'jobs', d.overdue > 0) +
      tile('Açık iş', d.open, d.on_the_way + ' usta yolda', '#0891b2', 'jobs') +
      tile('Bugün biten', d.done_today, tl(d.revenue_today) + ' ciro', '#16a34a', 'today') +
      tile('Tahsil edilecek', tl(d.receivable), d.receivable_n + ' iş · veresiye/kısmi', '#7c3aed', '/admin/accounting', d.receivable > 0) +
      (d.setup_missing ? tile('Kurulum eksiği', d.setup_missing, d.setup_critical ? d.setup_critical + ' kritik ayar' : 'Ayarları tamamlayın', d.setup_critical ? '#dc2626' : '#d97706', 'ek:kurulum', true) : '');
    if (box.__h !== h) { box.innerHTML = h; box.__h = h; }
  }
  function strip() {
    /* Bugün şeridi kaldırıldı (istek): varsa sil, yeniden oluşturma */
    var _old = document.getElementById('spx-bugun'); if (_old) _old.remove(); return;
    var on = isAdm() && location.pathname.replace(/\/$/, '') === '/admin';
    var dash = on && document.querySelector('[data-testid="admin-dashboard"]'), box = document.getElementById('spx-bugun');
    if (!dash) { if (box && !on) box.remove(); return; }
    if (!box || !dash.contains(box)) {
      if (box) box.remove();
      box = document.createElement('div'); box.id = 'spx-bugun'; box.className = 'notranslate';
      box.onclick = function (e) { var b = e.target.closest('[data-bg]'); if (!b) return; var a = b.getAttribute('data-bg'); if (a === 'today') jobs('today'); else if (a === 'jobs') jobs('15'); else go(a); };
      var hd = dash.firstElementChild; if (hd && hd.nextSibling) dash.insertBefore(box, hd.nextSibling); else dash.insertBefore(box, dash.firstChild);
      render();
    }
    load();
  }

  /* --- mobil hızlı işlem --- */
  var ACT = [['Yeni servis kaydı', '/admin/jobs', 'new-job-button', '#2563eb', '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>'], ['Yeni müşteri', '/admin/customers', 'new-customer-button', '#0891b2', '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0M19 8v6M16 11h6"/>'],
    ['Randevu', '/admin/appointments', 'new-appointment-button', '#7c3aed', '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'], ['Fiyat teklifi', '/admin/quotes', 'new-quote-button', '#db2777', '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M9 14h6M9 17h4"/>'], ['Tahsilat', 'ek:tahsilat', '', '#16a34a', '<rect x="2" y="6" width="20" height="13" rx="2"/><circle cx="12" cy="12.5" r="2.5"/><path d="M6 10v5M18 10v5"/>']];
  function clickWhenReady(tid, n) { var b = document.querySelector('[data-testid="' + tid + '"]'); if (b) { b.click(); return; } if (n > 0) setTimeout(function () { clickWhenReady(tid, n - 1); }, 250); }
  function fab() {
    var f = document.getElementById('spx-fab');
    if (!f) {
      f = document.createElement('button'); f.id = 'spx-fab'; f.className = 'notranslate'; f.setAttribute('aria-label', 'Hızlı işlem');
      f.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>';
      var m = document.createElement('div'); m.id = 'spx-fabm'; m.className = 'notranslate';
      m.innerHTML = ACT.map(function (a, i) { return '<button data-fa="' + i + '">' + a[0] + '<i style="background:' + a[3] + '"><svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' + a[4] + '</svg></i></button>'; }).join('');
      var bg = document.createElement('div'); bg.id = 'spx-fabbg';
      document.body.appendChild(bg); document.body.appendChild(m); document.body.appendChild(f);
      function tog(on) { f.classList.toggle('on', on); m.classList.toggle('on', on); bg.classList.toggle('on', on); }
      f.onclick = function () { tog(!m.classList.contains('on')); }; bg.onclick = function () { tog(false); };
      m.onclick = function (e) { var b = e.target.closest('[data-fa]'); if (!b) return; var a = ACT[+b.getAttribute('data-fa')]; tog(false); go(a[1]); if (a[2]) setTimeout(function () { clickWhenReady(a[2], 16); }, 300); };
    }
    var ovOn = !!document.querySelector('#spx-ov.on'), dlg = !!document.querySelector('[role="dialog"]');
    var ok = isAdm() && !/\/login/.test(location.pathname) && !ovOn && !dlg && !document.body.classList.contains('spx-nodel-fab');
    document.body.classList.toggle('spx-fabok', ok);
    if (!ok) { f.classList.remove('on'); var mm = document.getElementById('spx-fabm'); if (mm) mm.classList.remove('on'); var b2 = document.getElementById('spx-fabbg'); if (b2) b2.classList.remove('on'); }
  }
  setInterval(function () { try { strip(); fab(); } catch (e) { } }, 700);
})();

/* OnlineKaydet: platform sahibi (firmasiz yonetici) giris yapinca /sahip paneline git */
(function () {
  function go(txt) {
    try {
      var j = JSON.parse(txt);
      if (!j || !j.token) return;
      var c = JSON.parse(atob(j.token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
      if (c.role === 'admin' && !c.firm) { sessionStorage.setItem('ok_t', j.token); location.href = '/yonetim'; }
    } catch (e) { }
  }
  try {
    var xo = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (m, u) {
      var self = this;
      if (/\/auth\/login/.test(String(u)) && /POST/i.test(m)) {
        this.addEventListener('load', function () { if (self.status === 200) go(self.responseText); });
      }
      return xo.apply(this, arguments);
    };
    var of = window.fetch;
    window.fetch = function (u) {
      var p = of.apply(this, arguments);
      try {
        if (/\/auth\/login/.test(String(u && u.url || u))) p.then(function (r) { if (r.ok) r.clone().text().then(go); });
      } catch (e) { }
      return p;
    };
  } catch (e) { }
})();

/* OnlineKaydet: onceden giris yapmis platform sahibi de /sahip paneline gitsin */
(function () {
  try {
    var t = localStorage.getItem('token');
    if (!t || /^\/yonetim/.test(location.pathname)) return;
    var c = JSON.parse(atob(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    if (c.role === 'admin' && !c.firm) { sessionStorage.setItem('ok_t', t); location.replace('/yonetim'); }
  } catch (e) { }
})();
