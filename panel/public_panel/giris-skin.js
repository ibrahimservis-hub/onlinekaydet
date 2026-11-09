/* OnlineKaydet · personel giriş ekranı kaplaması: sağ sütun yeni görsel, ServisPlus logosu yerine OnlineKaydet. React'in kendi düğümlerine dokunmaz; yalnızca gizler ve yenisini ekler. */
(function () {
  var IMG = '/giris-gorsel.webp?v=1', LOGO = '/logo-renkli-s.png';
  function skin() {
    var h = [].slice.call(document.querySelectorAll('h1')).filter(function (e) { return /Hoş geldiniz/.test(e.textContent); })[0];
    if (!h) return;
    var root = h.closest('.min-h-screen');
    if (!root || root.getAttribute('data-ok-skin')) return;
    root.setAttribute('data-ok-skin', '1');
    [].forEach.call(root.querySelectorAll('img[src*="footer-logo"]'), function (i) {
      if (i.closest('.bg-slate-950')) return;
      i.src = LOGO; i.alt = 'OnlineKaydet';
    });
    [].forEach.call(root.querySelectorAll('*'), function (n) {
      if (n.children.length === 0 && /ServisPlus/.test(n.textContent) && !n.closest('.bg-slate-950')) n.textContent = n.textContent.replace(/ServisPlus/g, 'OnlineKaydet');
    });
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT), nd;
    while ((nd = w.nextNode())) { if (/Personel Giri/.test(nd.nodeValue)) nd.nodeValue = nd.nodeValue.replace(/Personel Giri[sş]i/, 'Üye girişi'); }
    var right = root.querySelector('.bg-slate-950');
    if (!right) return;
    [].forEach.call(right.children, function (c) { c.style.display = 'none'; });
    right.style.padding = '0';
    right.style.alignItems = 'flex-end';
    right.style.justifyContent = 'flex-start';
    var box = document.createElement('div');
    box.setAttribute('style', 'position:absolute;inset:0');
    box.innerHTML = '<img src="' + IMG + '" alt="OnlineKaydet servis yönetim ekranı" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:72% center">' +
      '<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(9,16,32,0) 45%,rgba(9,16,32,.82) 100%)"></div>' +
      '<div style="position:absolute;left:48px;right:48px;bottom:44px;color:#fff;max-width:520px">' +
      '<div style="font:700 11px/1 Inter,system-ui,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#f6a35c;margin-bottom:12px">OnlineKaydet</div>' +
      '<div style="font:700 28px/1.2 Inter,system-ui,sans-serif;letter-spacing:-.01em">Kayıt, usta ve tahsilat tek ekranda.</div>' +
      '<div style="font:400 14px/1.6 Inter,system-ui,sans-serif;color:#cdd6e4;margin-top:10px">Servis kayıtlarınızı, ustalarınızı ve müşterilerinizi telefondan da yönetin.</div></div>';
    right.appendChild(box);
  }
  var t = null;
  function sched() { if (t) return; t = setTimeout(function () { t = null; try { skin(); } catch (e) { } }, 60); }
  new MutationObserver(sched).observe(document.documentElement, { childList: true, subtree: true });
  sched();
})();
