/* RoutineFit PWA update repair (2026-10-25)
   Fixes stale homescreen views by preferring the latest network HTML.
   Keeps all user exercise data (localStorage, IndexedDB) untouched.
*/
const CACHE = 'routinefit-v1.1.1-navigation-network-first';
const CORE = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(CORE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key.startsWith('routinefit-') && key !== CACHE)
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET' || new URL(request.url).origin !== self.location.origin) return;

  if (request.mode === 'navigate' || request.destination === 'document') {
    event.respondWith((async () => {
      try {
        const response = await fetch(request, { cache: 'no-store' });
        if (response.ok) {
          const cache = await caches.open(CACHE);
          await cache.put(request, response.clone());
          // Keep the offline launch path up to date, including navigation with ?v=...
          const pathname = new URL(request.url).pathname;
          if (pathname.endsWith('/index.html') || pathname.endsWith('/')) {
            await cache.put('./index.html', response.clone());
          }
        }
        return response;
      } catch (_) {
        const cache = await caches.open(CACHE);
        return await cache.match(request, { ignoreSearch: true })
          || await cache.match('./index.html')
          || await cache.match('./')
          || new Response('인터넷 연결이 없고 저장된 화면도 없습니다.', { status: 503 });
      }
    })());
    return;
  }

  event.respondWith((async () => {
    const cached = await caches.match(request);
    if (cached) return cached;
    try {
      const response = await fetch(request);
      if (response.ok) {
        const cache = await caches.open(CACHE);
        await cache.put(request, response.clone());
      }
      return response;
    } catch (_) {
      return new Response('오프라인 파일이 없습니다.', { status: 503 });
    }
  })());
});
