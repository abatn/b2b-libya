/**
 * Libya B2B Platform - Cart Module
 * Server-side cart via /api/cart endpoints.
 */

const Cart = {
    async getAll() {
        try {
            const res = await fetch('/api/cart');
            if (res.status === 401 || res.status === 403) return [];
            if (!res.ok) return [];
            const data = await res.json();
            return data.items || [];
        } catch (e) {
            console.error('Cart fetch failed:', e);
            return [];
        }
    },

    async add(productId, quantity = 1, supplierId = null) {
        try {
            const body = { product_id: productId, quantity };
            if (supplierId) body.supplier_id = supplierId;
            const res = await fetch('/api/cart/items', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (!res.ok) {
                if (typeof showToast === 'function') {
                    showToast(data.detail || 'Failed to add to cart', 'error');
                }
                return null;
            }
            if (typeof showToast === 'function') {
                showToast('Added to cart', 'success');
            }
            await this.updateBadge();
            return data;
        } catch (e) {
            console.error('Cart add failed:', e);
            return null;
        }
    },

    async updateQuantity(itemId, quantity) {
        try {
            await fetch(`/api/cart/items/${itemId}?quantity=${quantity}`, { method: 'PUT' });
            await this.updateBadge();
        } catch (e) {
            console.error('Cart update failed:', e);
        }
    },

    async remove(itemId) {
        try {
            await fetch(`/api/cart/items/${itemId}`, { method: 'DELETE' });
            await this.updateBadge();
        } catch (e) {
            console.error('Cart remove failed:', e);
        }
    },

    async clear() {
        try {
            await fetch('/api/cart', { method: 'DELETE' });
            await this.updateBadge();
        } catch (e) {
            console.error('Cart clear failed:', e);
        }
    },

    async getTotal() {
        const items = await this.getAll();
        return items.reduce((sum, item) => sum + (item.product_price || 0) * item.quantity, 0);
    },

    async updateBadge() {
        const badge = document.getElementById('cart-badge');
        if (!badge) return;
        try {
            const res = await fetch('/api/cart');
            if (!res.ok) { badge.style.display = 'none'; return; }
            const data = await res.json();
            const count = data.item_count || 0;
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        } catch (e) {
            badge.style.display = 'none';
        }
    },

    async renderSummary(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        const items = await this.getAll();
        const total = items.reduce((sum, item) => sum + (item.product_price || 0) * item.quantity, 0);

        if (items.length === 0) {
            container.innerHTML = '<p style="text-align:center;color:#888;">Cart is empty</p>';
            const totalEl = document.getElementById('order-total');
            if (totalEl) totalEl.textContent = '0.00 LYD';
            return;
        }

        container.innerHTML = items.map(item => `
            <div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #eee;">
                <div>
                    <span>${item.product_name || 'Product'}</span>
                    ${item.supplier_name ? '<br><small style="color:#888;">by ' + item.supplier_name + '</small>' : ''}
                    ${!item.moq_met ? '<br><small style="color:var(--danger);">⚠️ Below MOQ (' + item.moq + ' min)</small>' : ''}
                </div>
                <div style="text-align:right;">
                    <span>${((item.product_price || 0) * item.quantity).toFixed(2)} LYD</span>
                    <br><small>x${item.quantity}</small>
                </div>
            </div>
        `).join('');

        const totalEl = document.getElementById('order-total');
        if (totalEl) totalEl.textContent = total.toFixed(2) + ' LYD';
    }
};
