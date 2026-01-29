// Journal Watcher Web App JavaScript

// Theme toggle
function toggleTheme() {
    const html = document.documentElement;
    const themeText = document.getElementById('theme-text');

    if (html.getAttribute('data-theme') === 'light') {
        html.setAttribute('data-theme', 'dark');
        if (themeText) themeText.textContent = 'Light Mode';
        localStorage.setItem('theme', 'dark');
    } else {
        html.setAttribute('data-theme', 'light');
        if (themeText) themeText.textContent = 'Dark Mode';
        localStorage.setItem('theme', 'light');
    }
}

// Load saved theme on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        const themeText = document.getElementById('theme-text');
        if (themeText) {
            themeText.textContent = savedTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
        }
    }
});

// HTMX event handling
document.body.addEventListener('htmx:afterRequest', function(evt) {
    // Handle errors
    if (!evt.detail.successful) {
        console.error('Request failed:', evt.detail.xhr.status);

        // Show error message if response is JSON
        try {
            const response = JSON.parse(evt.detail.xhr.responseText);
            if (response.detail) {
                alert('Error: ' + response.detail);
            }
        } catch (e) {
            // Not JSON, ignore
        }
    }
});

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 15px 25px;
        background: var(--header-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        box-shadow: var(--card-shadow);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
