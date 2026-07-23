// Deutsch Learning Hub - Service Worker
// CACHE_NAME below is auto-updated by build.py on every run — do not edit by hand.
// AUTO-CACHE-VERSION-START
const CACHE_NAME = 'deutsch-lernen-v20260723-134143';
// AUTO-CACHE-VERSION-END
const BASE = '/deutsch-lernen-goethe-a1-c2/';

// Static assets that rarely change (cache-first)
const STATIC_ASSETS = [
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
];

// Install: cache static assets only
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: clean ALL old caches immediately
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(names) {
      return Promise.all(
        names.filter(function(name) { return name !== CACHE_NAME; })
             .map(function(name) { return caches.delete(name); })
      );
    })
  );
  self.clients.claim();
});

// Fetch strategy:
// HTML pages: network-first (always get latest, cache as offline fallback)
// Static assets: cache-first (fast loading)
self.addEventListener('fetch', function(event) {
  var request = event.request;
  var url = new URL(request.url);

  // HTML pages and own assets: network-first
  if (request.mode === 'navigate' ||
      (url.origin === self.location.origin && url.pathname.startsWith(BASE))) {
    event.respondWith(
      fetch(request).then(function(networkResponse) {
        if (networkResponse && networkResponse.status === 200) {
          var responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(request, responseClone);
          });
        }
        return networkResponse;
      }).catch(function() {
        return caches.match(request).then(function(cachedResponse) {
          return cachedResponse || caches.match(BASE);
        });
      })
    );
    return;
  }

  // External static assets (CDN): cache-first
  event.respondWith(
    caches.match(request).then(function(cachedResponse) {
      if (cachedResponse) { return cachedResponse; }
      return fetch(request).then(function(networkResponse) {
        if (networkResponse && networkResponse.status === 200) {
          var responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(request, responseClone);
          });
        }
        return networkResponse;
      });
    })
  );
});
