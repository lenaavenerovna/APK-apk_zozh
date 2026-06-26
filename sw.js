// Service Worker для PWA
const CACHE_NAME = 'magic-health-v1';
const urlsToCache = [
  '/',
  '/static/icon-192.png',
  '/static/icon-512.png'
];

// Установка Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache открыт');
        return cache.addAll(urlsToCache);
      })
  );
});

// Активация и очистка старых кешей
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Перехват запросов и ответ из кеша
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Возвращаем кеш, если есть, иначе загружаем с сервера
        return response || fetch(event.request);
      })
  );
});