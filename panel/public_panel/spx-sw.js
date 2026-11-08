/* ServisPlus usta bildirimleri: push olaylarını gösterir, tıklayınca uygulamayı açar */
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (e) { e.waitUntil(self.clients.claim()); });
self.addEventListener('push', function (e) {
  var d = {}; try { d = e.data ? e.data.json() : {}; } catch (x) { try { d = { body: e.data.text() }; } catch (y) { } }
  e.waitUntil(self.registration.showNotification(d.title || 'ServisPlus', { body: d.body || '', icon: '/brand/logo.png', badge: '/brand/logo.png', data: { url: d.url || '/tech' }, vibrate: [200, 100, 200], requireInteraction: true, tag: 'sp-' + Date.now() }));
});
self.addEventListener('notificationclick', function (e) {
  e.notification.close(); var u = (e.notification.data && e.notification.data.url) || '/tech';
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (l) {
    for (var i = 0; i < l.length; i++) { if ('focus' in l[i]) { l[i].navigate && l[i].navigate(u); return l[i].focus(); } }
    return self.clients.openWindow(u);
  }));
});
