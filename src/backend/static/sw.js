/**
 * Libya B2B Platform — Service Worker
 * Offline-first caching strategy:
 *   - Static assets: Cache-First (fast, reliable)
 *   - API calls: Network-First (fresh data, fallback to cache)
 *   - HTML pages: Stale-While-Revalidate (fast + fresh)
 */

const CACHE_NAME = 'libya-b2b-v1';
const STATIC_CACHE = 'libya-b2b-static-v1';
const API_CACHE = 'libya-b2b-api-v1';

// Static assets to pre-cache on install
const PRECACHE_URLS = [
  '/',
  '/ar/',
  '/static/nav.css',
  '/static/nav.js',
  '/static/auth.js',
  '/static/cart.js',
  '/static/toast.js',
  '/static/manifest.json',
];

// ── Install: Pre-cache critical assets ──────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

// ── Activate: Clean old caches ─────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== STATIC_CACHE && key !== API_CACHE && key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch: Strategy router ─────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and chrome-extension
  if (request.method !== 'GET' || url.protocol === 'chrome-extension:') return;

  // API calls → Network-First
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Static assets → Cache-First
  if (url.pathname.startsWith('/static/') || url.pathname.endsWith('.js') || url.pathname.endsWith('.css')) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // HTML pages → Stale-While-Revalidate
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // Everything else → Cache-First
  event.respondWith(cacheFirst(request));
});

// ── Strategies ─────────────────────────────────────────────────────

/** Cache-First: Serve from cache, fallback to network */
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
  }
}

/** Network-First: Try network, fallback to cache */
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(API_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(
      JSON.stringify({ error: 'Offline', message: 'No network connection. Data may be outdated.' }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

/** Stale-While-Revalidate: Serve cache, update in background */
async function staleWhileRevalidate(request) {
  const cache = await caches.open(STATIC_CACHE);
  const cached = await cache.match(request);

  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(() => cached);

  return cached || fetchPromise;
}

// ── Background Sync (for offline actions) ──────────────────────────
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-pending-orders') {
    event.waitUntil(syncPendingOrders());
  }
});

async function syncPendingOrders() {
  // Read pending actions from IndexedDB and replay them
  // This will be called when the user comes back online
  const clients = await self.clients.matchAll();
  clients.forEach((client) => {
    client.postMessage({ type: 'SYNC_COMPLETE' });
  });
}

// ── Push Notifications ─────────────────────────────────────────────
self.addEventListener('push', (event) => {
  if (!event.data) return;
  const data = event.data.json();
  const title = data.title || data.title_ar || 'Libya B2B';
  const body = data.body || data.body_ar || 'You have a new notification';
  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon: '/static/icons/icon-192.png',
      badge: '/static/icons/icon-192.png',
      tag: data.tag || 'libya-b2b',
      data: data.url || '/',
      actions: [
        { action: 'open', title: 'View' },
        { action: 'dismiss', title: 'Dismiss' },
      ],
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.action === 'dismiss') return;
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      // Focus existing window or open new one
      for (const client of clients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.focus();
          client.navigate(event.notification.data || '/');
          return;
        }
      }
      self.clients.openWindow(event.notification.data || '/');
    })
  );
});
