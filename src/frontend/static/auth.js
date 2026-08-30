/**
 * Libya B2B Platform - Auth Client
 * Session-based authentication helpers.
 */

/* ── i18n: detect language from URL and provide modal labels ── */
const _authBase = window.location.pathname.startsWith('/ar/') ? '/ar' : '';
const _authLang = _authBase ? 'ar' : 'en';
const _authI18n = {
    en: {
        title: 'Login / Register',
        username: 'Username',
        password: 'Password',
        remember_me: 'Remember me',
        login_btn: 'Login',
        register_btn: 'Register',
        cancel: 'Cancel',
        welcome: 'Welcome back',
    },
    ar: {
        title: 'تسجيل الدخول / التسجيل',
        username: 'اسم المستخدم',
        password: 'كلمة المرور',
        remember_me: 'تذكرني',
        login_btn: 'تسجيل الدخول',
        register_btn: 'تسجيل',
        cancel: 'الغاء',
        welcome: 'مرحبا بعودتك',
    },
};
function _authT(key) {
    return (_authI18n[_authLang] || _authI18n.en)[key] || key;
}

const Auth = {
    async register(data) {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error((await res.json()).detail || 'Registration failed');
        return res.json();
    },

    async login(username, password, rememberMe = false) {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, remember_me: rememberMe }),
        });
        if (!res.ok) throw new Error((await res.json()).detail || 'Login failed');
        return res.json();
    },

    async logout() {
        await fetch('/api/auth/logout', { method: 'POST' });
    },

    /**
     * Global logout handler — used by all templates.
     */
    handleLogout(e) {
        if (e) e.preventDefault();
        Auth.logout().then(() => location.reload());
    },

    async me() {
        const res = await fetch('/api/auth/me');
        if (!res.ok) return null;
        return res.json();
    },

    showLoginModal() {
        const modal = document.createElement('div');
        modal.id = 'auth-modal';
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
        modal.innerHTML = `
            <div style="background:white;border-radius:12px;padding:30px;max-width:400px;width:90%;box-shadow:0 4px 20px rgba(0,0,0,0.3);direction:${_authLang === 'ar' ? 'rtl' : 'ltr'};">
                <h3 style="margin-bottom:20px;text-align:center;">${_authT('title')}</h3>
                <div style="margin-bottom:15px;">
                    <input type="text" id="auth-username" placeholder="${_authT('username')}" style="width:100%;padding:12px;border:2px solid #ddd;border-radius:8px;margin-bottom:10px;">
                    <input type="password" id="auth-password" placeholder="${_authT('password')}" style="width:100%;padding:12px;border:2px solid #ddd;border-radius:8px;margin-bottom:10px;">
                    <label style="display:flex;align-items:center;gap:8px;font-size:0.9rem;color:#666;">
                        <input type="checkbox" id="auth-remember"> ${_authT('remember_me')}
                    </label>
                </div>
                <div style="display:flex;gap:10px;">
                    <button id="auth-login-btn" style="flex:1;padding:12px;background:#00d2ff;color:white;border:none;border-radius:8px;font-weight:bold;cursor:pointer;">${_authT('login_btn')}</button>
                    <a href="${_authBase}/register" style="flex:1;padding:12px;background:#ff6a00;color:white;border:none;border-radius:8px;font-weight:bold;cursor:pointer;text-align:center;text-decoration:none;display:flex;align-items:center;justify-content:center;">${_authT('register_btn')}</a>
                </div>
                <button onclick="document.getElementById('auth-modal').remove()" style="width:100%;padding:10px;background:none;border:none;color:#888;cursor:pointer;margin-top:10px;">${_authT('cancel')}</button>
            </div>`;
        document.body.appendChild(modal);

        document.getElementById('auth-login-btn').onclick = async () => {
            try {
                const user = await Auth.login(
                    document.getElementById('auth-username').value,
                    document.getElementById('auth-password').value,
                    document.getElementById('auth-remember').checked
                );
                modal.remove();
                if (typeof showToast === 'function') showToast(_authT('welcome') + ', ' + user.user.username + '!', 'success');
                setTimeout(() => location.reload(), 500);
            } catch (e) {
                if (typeof showToast === 'function') showToast(e.message, 'error');
            }
        };
    },

    updateNavAuth(currentUser) {
        const authBtn = document.getElementById('auth-nav-btn');
        if (!authBtn) return;
        if (currentUser) {
            authBtn.textContent = currentUser.username;
            authBtn.onclick = async () => { await Auth.logout(); location.reload(); };
            authBtn.title = 'Click to logout';
        } else {
            authBtn.textContent = _authT('login_btn');
            authBtn.onclick = () => Auth.showLoginModal();
        }
    },

    /**
     * Require authentication and optional role check.
     * @param {string|null} expectedRole - 'buyer', 'seller', or null for any
     * @returns {Promise<Object|null>} user object or null if redirected to login
     */
    async requireAuth(expectedRole) {
        const user = await Auth.me();
        if (!user) {
            Auth.showLoginModal();
            return null;
        }
        if (expectedRole && user.role !== expectedRole) {
            const msg = expectedRole === 'seller'
                ? (_authLang === 'ar' ? 'هذه الصفحة للموردين فقط.' : 'Diese Seite ist nur für Verkäufer (Seller) zugänglich.')
                : (_authLang === 'ar' ? 'هذه الصفحة للمشترين فقط.' : 'Diese Seite ist nur für Käufer (Buyer) zugänglich.');
            if (typeof showToast === 'function') {
                showToast(msg, 'error');
            } else {
                alert(msg);
            }
            return null;
        }
        return user;
    }
};

// Global logout handler — used by onclick="handleLogout(event)" in all templates
function handleLogout(e) {
    if (e) e.preventDefault();
    Auth.logout().then(() => location.reload());
}
