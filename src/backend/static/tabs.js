/**
 * Libya B2B Platform - Tab System
 * Replaces inline onclick="switchTab()" handlers.
 */

function initTabs(containerSelector) {
    const container = document.querySelector(containerSelector || '.tabs');
    if (!container) return;

    container.addEventListener('click', (e) => {
        const tab = e.target.closest('.tab');
        if (!tab) return;
        const tabName = tab.dataset.tab;
        if (!tabName) return;

        // Deactivate all tabs
        container.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Show matching content
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        const target = document.getElementById('tab-' + tabName);
        if (target) target.classList.add('active');
    });
}
