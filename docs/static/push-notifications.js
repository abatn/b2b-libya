/**
 * Libya B2B Platform — Push Notifications Client
 * Handles permission request, subscription, and in-app notification UI.
 */

(function() {
  'use strict';

  const PushNotify = {
    _permission: 'default',
    _subscription: null,

    // ── Initialize ────────────────────────────────────────
    async init() {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.log('[Push] Push API not supported');
        return;
      }

      this._permission = Notification.permission;
      this._updateBellBadge();

      // Listen for SW messages
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data.type === 'SYNC_COMPLETE') {
          this._updateBellBadge();
        }
      });

      // Refresh badge every 60 seconds
      setInterval(() => this._updateBellBadge(), 60000);
    },

    // ── Request Permission ────────────────────────────────
    async requestPermission() {
      if (!('Notification' in window)) {
        console.log('[Push] Notifications not supported');
        return 'denied';
      }

      if (this._permission === 'granted') return 'granted';

      const result = await Notification.requestPermission();
      this._permission = result;

      if (result === 'granted') {
        await this._subscribe();
      }

      return result;
    },

    // ── Subscribe to Push ─────────────────────────────────
    async _subscribe() {
      try {
        // Fetch VAPID public key from server
        const keyRes = await fetch(`${window.API_BASE}/api/notifications/vapid-public-key`);
        if (!keyRes.ok) {
          console.log('[Push] VAPID key not available — push disabled');
          return;
        }
        const { publicKey } = await keyRes.json();
        if (!publicKey) return;

        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this._urlBase64ToUint8Array(publicKey),
        });

        this._subscription = subscription;
        await this._sendSubscriptionToServer(subscription);
        console.log('[Push] Subscribed successfully');
      } catch (e) {
        console.error('[Push] Subscription failed:', e);
      }
    },

    // ── Unsubscribe ───────────────────────────────────────
    async unsubscribe() {
      try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        if (subscription) {
          await subscription.unsubscribe();
        }
        await fetch(`${window.API_BASE}/api/notifications/unsubscribe`, { method: 'DELETE' });
        this._subscription = null;
        console.log('[Push] Unsubscribed');
      } catch (e) {
        console.error('[Push] Unsubscribe failed:', e);
      }
    },

    // ── Send subscription to server ───────────────────────
    async _sendSubscriptionToServer(subscription) {
      const json = subscription.toJSON();
      await fetch(`${window.API_BASE}/api/notifications/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: json.endpoint,
          p256dh: json.keys.p256dh,
          auth: json.keys.auth,
          user_agent: navigator.userAgent,
        }),
      });
    },

    // ── Load Notifications ────────────────────────────────
    async loadNotifications() {
      try {
        const res = await fetch(`${window.API_BASE}/api/notifications?limit=10`);
        if (!res.ok) return [];
        return await res.json();
      } catch {
        return [];
      }
    },

    // ── Update Bell Badge ─────────────────────────────────
    async _updateBellBadge() {
      try {
        const res = await fetch(`${window.API_BASE}/api/notifications/unread-count`);
        if (!res.ok) return;
        const { count } = await res.json();

        const badge = document.getElementById('navMsgBadge');
        if (badge) {
          badge.textContent = count || '';
          badge.style.display = count > 0 ? 'inline-flex' : 'none';
        }
      } catch {
        // Silently fail
      }
    },

    // ── Mark as Read ─────────────────────────────────────
    async markRead(notificationId) {
      await fetch(`${window.API_BASE}/api/notifications/${notificationId}/read`, { method: 'POST' });
      this._updateBellBadge();
    },

    // ── Mark All Read ────────────────────────────────────
    async markAllRead() {
      await fetch(`${window.API_BASE}/api/notifications/read-all`, { method: 'POST' });
      this._updateBellBadge();
    },

    // ── Show In-App Notification ──────────────────────────
    showNotification(title, body, url) {
      // Try native notification first
      if (this._permission === 'granted') {
        const n = new Notification(title, {
          body,
          icon: '/static/icons/icon-192.png',
          badge: '/static/icons/icon-192.png',
          tag: 'libya-b2b',
          data: url || '/',
        });
        n.onclick = () => {
          window.open(url || '/', '_blank');
          n.close();
        };
      }

      // Also show toast
      if (window.Toast) {
        window.Toast.show(`${title}: ${body}`, 'info');
      }
    },

    // ── Helpers ───────────────────────────────────────────
    _urlBase64ToUint8Array(base64String) {
      if (!base64String) return new Uint8Array(0);
      const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
      const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
      const rawData = window.atob(base64);
      return Uint8Array.from([...rawData].map(char => char.charCodeAt(0)));
    },
  };

  // Expose globally
  window.PushNotify = PushNotify;

  // Auto-init on load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => PushNotify.init());
  } else {
    PushNotify.init();
  }
})();
