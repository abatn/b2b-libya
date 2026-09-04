/**
 * Libya B2B — Shared Navigation JavaScript
 * Handles: auth, categories, autocomplete, notifications, breadcrumb
 * Layer 1 (nav-top) = Core: Logo + Search + Cart + Account
 * Layer 2 (nav-main) = Utility: My Account + Register + Help + Language
 */

(function() {
    'use strict';

    const _base =
        window.SITE_BASE +
        (window.location.pathname.startsWith(window.SITE_BASE + '/ar/') ||
         window.location.pathname === window.SITE_BASE + '/ar' ? '/ar' : '');

    // ═══════════════════════════════════════════════════════════════
    // 1. AUTH CHECK — Toggle Register/Sign In vs My Account + Role
    // ═══════════════════════════════════════════════════════════════
    let currentUserRole = null;

    async function checkAuth() {
        try {
            const user = await Auth.me();
            const avatarEl = document.getElementById('auth-nav-avatar');
            const utilityBar = document.getElementById('navLayer2');
            const myAccountDropdown = document.getElementById('myAccountDropdown');
            const buyerMenu = document.getElementById('accountMenu');
            const sellerMenu = document.getElementById('accountMenuSeller');
            const topBuyerMenu = document.getElementById('myAccountMenu');
            const topSellerMenu = document.getElementById('myAccountMenuSeller');
            const topAccountLink = document.getElementById('topAccountLink');
            const hamburger = document.getElementById('navHamburger');
            if (!avatarEl) return;

            if (user) {
                currentUserRole = user.role || 'buyer';
                const initial = (user.username || user.email || 'U').charAt(0).toUpperCase();
                avatarEl.textContent = initial;
                avatarEl.onclick = (e) => {
                    e.preventDefault();
                    const activeMenu = currentUserRole === 'seller' ? sellerMenu : buyerMenu;
                    if (activeMenu) activeMenu.classList.toggle('show');
                };

                // Top Account Link — role-based (in Layer 2 utility bar)
                if (topAccountLink) {
                    topAccountLink.onclick = (e) => {
                        e.preventDefault();
                        const activeTopMenu = currentUserRole === 'seller' ? topSellerMenu : topBuyerMenu;
                        if (activeTopMenu) activeTopMenu.classList.toggle('show');
                    };
                }

                // Hamburger — toggle Layer 2 utility bar on mobile
                if (hamburger) {
                    hamburger.onclick = () => {
                        if (utilityBar) utilityBar.classList.toggle('show');
                    };
                }

                // Show utility bar items when logged in
                if (myAccountDropdown) myAccountDropdown.style.display = '';
                if (utilityBar) {
                    Array.from(utilityBar.querySelectorAll('a, span')).forEach(c => {
                        if (c.tagName === 'A' && !c.classList.contains('lang-btn-top') && !c.classList.contains('nav-top-account')) {
                            if (c.textContent.includes('Register') || c.textContent.includes('Sign In') || c.textContent.includes('تسجيل'))
                                c.style.display = 'none';
                        }
                        if (c.classList && c.classList.contains('nav-divider')) {
                            const prev = c.previousElementSibling;
                            if (prev && prev.style && prev.style.display === 'none') c.style.display = 'none';
                        }
                    });
                }

                // Role-based dropdown switching
                if (currentUserRole === 'seller') {
                    if (buyerMenu) buyerMenu.style.display = 'none';
                    if (sellerMenu) sellerMenu.style.display = '';
                    if (topBuyerMenu) topBuyerMenu.style.display = 'none';
                    if (topSellerMenu) topSellerMenu.style.display = '';
                } else {
                    if (buyerMenu) buyerMenu.style.display = '';
                    if (sellerMenu) sellerMenu.style.display = 'none';
                    if (topBuyerMenu) topBuyerMenu.style.display = '';
                    if (topSellerMenu) topSellerMenu.style.display = 'none';
                }
            } else {
                currentUserRole = null;
                avatarEl.onclick = (e) => { e.preventDefault(); Auth.showLoginModal(); };
                if (topAccountLink) {
                    topAccountLink.onclick = (e) => { e.preventDefault(); Auth.showLoginModal(); };
                }
                if (myAccountDropdown) myAccountDropdown.style.display = 'none';
            }
        } catch (err) { console.error('Auth check failed:', err); }
    }

    // ═══════════════════════════════════════════════════════════════
    // 2. LOAD CATEGORIES — Populate dropdown + Layer 3 tabs
    // ═══════════════════════════════════════════════════════════════
    async function loadCategories() {
        try {
            const res = await fetch(`${window.API_BASE}/api/b2b/categories`);
            const cats = await res.json();
            if (!Array.isArray(cats)) return;

            const select = document.getElementById('navCatSelect');
            const catList = document.getElementById('navCatList');
            if (!select && !catList) return;

            // Populate dropdown
            if (select) {
                cats.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id;
                    opt.textContent = c.icon + ' ' + (_base ? (c.name_ar || c.name_en) : c.name_en);
                    select.appendChild(opt);
                });
            }

            // Populate Layer 3 tabs with flyout
            if (catList) {
                const lang = _base ? 'ar' : 'en';
                const nameLabel = lang === 'ar' ? 'name_ar' : 'name_en';
                cats.forEach(c => {
                    const a = document.createElement('a');
                    a.href = _base + '/b2b/products?category=' + c.id;
                    a.className = 'nav-cat-item';
                    const subcats = (c.subcategories || []).slice(0, 8);
                    let flyoutHtml = '';
                    if (subcats.length > 0) {
                        flyoutHtml = '<div class="nav-cat-flyout">' +
                            subcats.map(s => '<a href="' + _base + '/b2b/products?category=' + c.id + '&sub=' + s.id + '">' +
                                (s.icon || '') + ' ' + (s[nameLabel] || s.name_en || '') + '</a>').join('') +
                            '</div>';
                    }
                    a.innerHTML = '<span class="cat-emoji">' + (c.icon || '') + '</span> ' + (c[nameLabel] || c.name_en) + flyoutHtml;
                    catList.appendChild(a);
                });
            }
        } catch (e) { console.error('Categories load failed:', e); }
    }

    // ═══════════════════════════════════════════════════════════════
    // 3. SEARCH AUTOCOMPLETE
    // ═══════════════════════════════════════════════════════════════
    let acTimeout = null;
    function setupAutocomplete() {
        const input = document.getElementById('navSearchInput');
        const dropdown = document.getElementById('navAutocomplete');
        if (!input || !dropdown) return;

        input.addEventListener('input', function() {
            clearTimeout(acTimeout);
            const q = this.value.trim();
            if (q.length < 2) { dropdown.classList.remove('show'); return; }

            acTimeout = setTimeout(async () => {
                try {
                    const res = await fetch(`${window.API_BASE}/api/b2b/products?search=${encodeURIComponent(q}`);
                    const data = await res.json();
                    const products = data.products || [];
                    if (!products.length) { dropdown.classList.remove('show'); return; }

                    const html = '<div class="nav-autocomplete-header">Products</div>' +
                        products.map(p => {
                            const name = _base ? (p.name_ar || p.name) : p.name;
                            const highlighted = name.replace(new RegExp('(' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi'), '<span class="ac-highlight">$1</span>');
                            return '<div class="nav-autocomplete-item" onclick="window.location.href=\'' + _base + '/b2b/products?search=' + encodeURIComponent(p.name) + '\'">' +
                                '<svg class="ac-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>' +
                                highlighted + '</div>';
                        }).join('');

                    dropdown.innerHTML = html;
                    dropdown.classList.add('show');
                } catch (e) { console.error('Autocomplete error:', e); }
            }, 300);
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.nav-top-search')) {
                dropdown.classList.remove('show');
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════
    // 4. NOTIFICATION BADGE
    // ═══════════════════════════════════════════════════════════════
    async function loadNotifications() {
        try {
            const res = await fetch(`${window.API_BASE}/api/b2b/messages/unread-count`);
            if (res.ok) {
                const data = await res.json();
                const badge = document.getElementById('navMsgBadge');
                if (badge && data.count > 0) {
                    badge.textContent = data.count > 99 ? '99+' : data.count;
                }
            }
        } catch (e) { /* silent */ }

        // Also load push notification count
        try {
            const notifRes = await fetch(`${window.API_BASE}/api/notifications/unread-count`);
            if (notifRes.ok) {
                const notifData = await notifRes.json();
                if (notifData.count > 0) {
                    const badge = document.getElementById('navMsgBadge');
                    if (badge) {
                        const existing = parseInt(badge.textContent) || 0;
                        const total = existing + notifData.count;
                        badge.textContent = total > 99 ? '99+' : total;
                        badge.style.display = 'inline-flex';
                    }
                }
            }
        } catch (e) { /* silent */ }
    }

    // ═══════════════════════════════════════════════════════════════
    // 5. BREADCRUMB — Auto-generate from path
    // ═══════════════════════════════════════════════════════════════
    function generateBreadcrumb() {
        const el = document.getElementById('breadcrumb');
        if (!el) return;

        const rawPath = window.location.pathname;
        const path = rawPath
            .replace(new RegExp('^' + window.SITE_BASE), '')
            .replace(/^\/ar\//, '/')
            .replace(/\/$/, '') || '/';
        const segments = path.split('/').filter(Boolean);
        const lang = (rawPath.startsWith(window.SITE_BASE + '/ar') ||
                      rawPath === window.SITE_BASE + '/ar') ? 'ar' : 'en';
        const isAr = lang === 'ar';

        const labels = {
            '': isAr ? 'الرئيسية' : 'Home',
            'b2b': 'B2B',
            'products': isAr ? 'المنتجات' : 'Products',
            'suppliers': isAr ? 'الموردون' : 'Suppliers',
            'rfq': isAr ? 'طلب عرض سعر' : 'RFQ',
            'cart': isAr ? 'سلة التسوق' : 'Cart',
            'tracking': isAr ? 'تتبع الطلب' : 'Track Order',
            'escrow': isAr ? 'ضمان الدفع' : 'Escrow',
            'messages': isAr ? 'الرسائل' : 'Messages',
            'buyer': isAr ? 'لوحة المشتري' : 'Buyer Dashboard',
            'seller': isAr ? 'لوحة البائع' : 'Seller Dashboard',
            'checkout': isAr ? 'إتمام الطلب' : 'Checkout',
        };

        let html = '<a href="' + _base + '/">' + (isAr ? 'الرئيسية' : 'Home') + '</a>';
        let currentPath = '';
        segments.forEach((seg, i) => {
            currentPath += '/' + seg;
            const label = labels[seg] || seg;
            const isLast = i === segments.length - 1;
            html += '<span>›</span>';
            if (isLast) {
                html += '<span class="bc-current">' + label + '</span>';
            } else {
                html += '<a href="' + _base + currentPath + '">' + label + '</a>';
            }
        });

        el.innerHTML = html;
    }

    // ═══════════════════════════════════════════════════════════════
    // 6. NAV SEARCH
    // ═══════════════════════════════════════════════════════════════
    window.navSearch = function() {
        const q = document.getElementById('navSearchInput').value.trim();
        if (!q) return;
        const cat = document.getElementById('navCatSelect').value;
        let url = _base + '/b2b/products?search=' + encodeURIComponent(q);
        if (cat && cat !== 'all') url += '&category=' + cat;
        window.location.href = url;
    };

    // ═══════════════════════════════════════════════════════════════
    // 7. CART COUNT
    // ═══════════════════════════════════════════════════════════════
    function loadCartCount() {
        fetch(`${window.API_BASE}/api/cart/items`)
            .then(r => r.ok ? r.json() : {items: []})
            .then(data => {
                const count = (data.items || []).reduce((sum, item) => sum + (item.quantity || 1), 0);
                const badge = document.getElementById('navCartBadge');
                if (count > 0 && badge) badge.textContent = count;
            })
            .catch(() => { /* silent fallback */ });
    }

    // ═══════════════════════════════════════════════════════════════
    // 8. OUTSIDE CLICK — Close all dropdowns
    // ═══════════════════════════════════════════════════════════════
    document.addEventListener('click', (e) => {
        // Close Layer 1 avatar menus
        const accountDropdown = document.getElementById('accountDropdown');
        const buyerMenu = document.getElementById('accountMenu');
        const sellerMenu = document.getElementById('accountMenuSeller');
        if (accountDropdown && !accountDropdown.contains(e.target)) {
            if (buyerMenu) buyerMenu.classList.remove('show');
            if (sellerMenu) sellerMenu.classList.remove('show');
        }
        // Close Layer 2 utility menus
        const myDropdown = document.getElementById('myAccountDropdown');
        const topBuyerMenu = document.getElementById('myAccountMenu');
        const topSellerMenu = document.getElementById('myAccountMenuSeller');
        if (myDropdown && !myDropdown.contains(e.target)) {
            if (topBuyerMenu) topBuyerMenu.classList.remove('show');
            if (topSellerMenu) topSellerMenu.classList.remove('show');
        }
    });

    // ═══════════════════════════════════════════════════════════════
    // INIT — Run on DOM ready
    // ═══════════════════════════════════════════════════════════════
    document.addEventListener('DOMContentLoaded', () => {
        checkAuth();
        loadCategories();
        setupAutocomplete();
        loadNotifications();
        loadCartCount();
        generateBreadcrumb();

        // Search on Enter
        const searchInput = document.getElementById('navSearchInput');
        if (searchInput) {
            searchInput.addEventListener('keypress', e => { if (e.key === 'Enter') navSearch(); });
        }
    });

})();
