// Deutsch Learning Hub - Service Worker
const CACHE_NAME = 'deutsch-lernen-v1';
const BASE = '/deutsch-lernen-goethe-a1-c2/';

const URLS_TO_CACHE = ['/deutsch-lernen-goethe-a1-c2/', '/deutsch-lernen-goethe-a1-c2/A1/01_Wortschatz.html', '/deutsch-lernen-goethe-a1-c2/A1/02_Grammatik.html', '/deutsch-lernen-goethe-a1-c2/A1/03_Saetze.html', '/deutsch-lernen-goethe-a1-c2/A1/04_Lesen.html', '/deutsch-lernen-goethe-a1-c2/A1/05_Hoeren.html', '/deutsch-lernen-goethe-a1-c2/A1/06_Sprechen.html', '/deutsch-lernen-goethe-a1-c2/A1/07_Schreiben.html', '/deutsch-lernen-goethe-a1-c2/A1/08_Musterpruefung.html', '/deutsch-lernen-goethe-a1-c2/A1/README.html', '/deutsch-lernen-goethe-a1-c2/A1/index.html', '/deutsch-lernen-goethe-a1-c2/A2/01_Wortschatz.html', '/deutsch-lernen-goethe-a1-c2/A2/02_Grammatik.html', '/deutsch-lernen-goethe-a1-c2/A2/03_Saetze.html', '/deutsch-lernen-goethe-a1-c2/A2/04_Lesen.html', '/deutsch-lernen-goethe-a1-c2/A2/05_Hoeren.html', '/deutsch-lernen-goethe-a1-c2/A2/06_Sprechen.html', '/deutsch-lernen-goethe-a1-c2/A2/07_Schreiben.html', '/deutsch-lernen-goethe-a1-c2/A2/08_Musterpruefung.html', '/deutsch-lernen-goethe-a1-c2/A2/README.html', '/deutsch-lernen-goethe-a1-c2/A2/index.html', '/deutsch-lernen-goethe-a1-c2/B1/01_Wortschatz.html', '/deutsch-lernen-goethe-a1-c2/B1/02_Grammatik.html', '/deutsch-lernen-goethe-a1-c2/B1/03_Saetze.html', '/deutsch-lernen-goethe-a1-c2/B1/04_Lesen.html', '/deutsch-lernen-goethe-a1-c2/B1/05_Hoeren.html', '/deutsch-lernen-goethe-a1-c2/B1/06_Sprechen.html', '/deutsch-lernen-goethe-a1-c2/B1/07_Schreiben.html', '/deutsch-lernen-goethe-a1-c2/B1/08_Musterpruefung.html', '/deutsch-lernen-goethe-a1-c2/B1/README.html', '/deutsch-lernen-goethe-a1-c2/B1/index.html', '/deutsch-lernen-goethe-a1-c2/B2/01_Wortschatz.html', '/deutsch-lernen-goethe-a1-c2/B2/02_Grammatik.html', '/deutsch-lernen-goethe-a1-c2/B2/03_Saetze.html', '/deutsch-lernen-goethe-a1-c2/B2/04_Lesen.html', '/deutsch-lernen-goethe-a1-c2/B2/05_Hoeren.html', '/deutsch-lernen-goethe-a1-c2/B2/06_Sprechen.html', '/deutsch-lernen-goethe-a1-c2/B2/07_Schreiben.html', '/deutsch-lernen-goethe-a1-c2/B2/08_Musterpruefung.html', '/deutsch-lernen-goethe-a1-c2/B2/README.html', '/deutsch-lernen-goethe-a1-c2/B2/index.html', '/deutsch-lernen-goethe-a1-c2/C1/01_Wortschatz.html', '/deutsch-lernen-goethe-a1-c2/C1/02_Grammatik.html', '/deutsch-lernen-goethe-a1-c2/C1/03_Saetze.html', '/deutsch-lernen-goethe-a1-c2/C1/04_Lesen.html', '/deutsch-lernen-goethe-a1-c2/C1/05_Hoeren.html', '/deutsch-lernen-goethe-a1-c2/C1/06_Sprechen.html', '/deutsch-lernen-goethe-a1-c2/C1/07_Schreiben.html', '/deutsch-lernen-goethe-a1-c2/C1/08_Musterpruefung.html', '/deutsch-lernen-goethe-a1-c2/C1/README.html', '/deutsch-lernen-goethe-a1-c2/C1/index.html', '/deutsch-lernen-goethe-a1-c2/C2/01_Wortschatz.html', '/deutsch-lernen-goethe-a1-c2/C2/02_Grammatik.html', '/deutsch-lernen-goethe-a1-c2/C2/03_Saetze.html', '/deutsch-lernen-goethe-a1-c2/C2/04_Lesen.html', '/deutsch-lernen-goethe-a1-c2/C2/05_Hoeren.html', '/deutsch-lernen-goethe-a1-c2/C2/06_Sprechen.html', '/deutsch-lernen-goethe-a1-c2/C2/07_Schreiben.html', '/deutsch-lernen-goethe-a1-c2/C2/08_Musterpruefung.html', '/deutsch-lernen-goethe-a1-c2/C2/README.html', '/deutsch-lernen-goethe-a1-c2/C2/index.html', '/deutsch-lernen-goethe-a1-c2/index.html', '/deutsch-lernen-goethe-a1-c2/manifest.json', '/deutsch-lernen-goethe-a1-c2/icon-192x192.png', '/deutsch-lernen-goethe-a1-c2/icon-512x512.png', '/deutsch-lernen-goethe-a1-c2/og-image.png', '/deutsch-lernen-goethe-a1-c2/header.html', '/deutsch-lernen-goethe-a1-c2/footer.html', '/deutsch-lernen-goethe-a1-c2/jump_grammatik.html', '/deutsch-lernen-goethe-a1-c2/jump_saetze.html', '/deutsch-lernen-goethe-a1-c2/jump_wortschatz.html'];

// Install: cache all pages
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(URLS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate: clean old caches
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

// Fetch: serve from cache, fall back to network
self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request).then(function(response) {
      if (response) { return response; }
      return fetch(event.request).then(function(networkResponse) {
        // Cache new requests dynamically (e.g. Bootstrap CDN)
        if (networkResponse && networkResponse.status === 200) {
          var responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(event.request, responseClone);
          });
        }
        return networkResponse;
      }).catch(function() {
        // Offline fallback for navigation requests
        if (event.request.mode === 'navigate') {
          return caches.match(BASE);
        }
      });
    })
  );
});
