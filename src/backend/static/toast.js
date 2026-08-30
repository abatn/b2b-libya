/**
 * Libya B2B Platform - Toast Notification System
 * Replaces all alert() calls with user-friendly notifications.
 */

function showToast(message, type = 'info', duration = 3000) {
    // Remove existing toasts
    document.querySelectorAll('.b2b-toast').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = 'b2b-toast';
    toast.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 10000;
        padding: 14px 24px; border-radius: 10px; color: white;
        font-family: 'Segoe UI', Tahoma, sans-serif; font-size: 0.95rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25); max-width: 400px;
        animation: toastSlideIn 0.3s ease; cursor: pointer;
    `;

    const colors = {
        info: '#00d2ff',
        success: '#28a745',
        warning: '#ffc107',
        error: '#dc3545',
    };
    toast.style.background = colors[type] || colors.info;

    // Add icon
    const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌' };
    toast.innerHTML = `<span>${icons[type] || ''}</span> ${message}`;

    toast.onclick = () => toast.remove();
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Add animation styles
if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        @keyframes toastSlideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
}
