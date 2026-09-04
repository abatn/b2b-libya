/**
 * Libya B2B Platform — Service Worker Registration
 * Registers the SW for offline support and manages updates.
 */

(function() {
  'use strict';

  if (!('serviceWorker' in navigator)) {
    console.log('[PWA] Service Worker not supported');
    return;
  }

  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/static/sw.js', {
        scope: '/'
      });

      console.log('[PWA] Registered:', registration.scope);

      // Check for updates every 60 minutes
      setInterval(() => {
        registration.update();
      }, 60 * 60 * 1000);

      // Handle updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'activated') {
            // Notify user of update
            if (window.Toast) {
              window.Toast.show('App updated! Refresh for the latest version.', 'info');
            }
          }
        });
      });

      // Listen for sync complete messages from SW
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data.type === 'SYNC_COMPLETE') {
          console.log('[PWA] Background sync complete');
          if (window.Toast) {
            window.Toast.show('Data synced successfully!', 'success');
          }
          // Refresh any pending data
          window.dispatchEvent(new Event('pwa-sync-complete'));
        }
      });

    } catch (error) {
      console.log('[PWA] Registration failed:', error);
    }
  });

  // Online/Offline status indicator
  function updateOnlineStatus() {
    const isOnline = navigator.onLine;
    document.body.classList.toggle('offline', !isOnline);
    document.body.classList.toggle('online', isOnline);

    if (!isOnline && window.Toast) {
      window.Toast.show('You are offline. Changes will sync when reconnected.', 'warning');
    }
  }

  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
  updateOnlineStatus();
})();
