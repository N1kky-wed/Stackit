// static/js/theme.js

function applyTheme(theme) {
    const body = document.body;
    const themeIcon = document.getElementById('themeIcon');
    if (theme === 'dark') {
        body.classList.remove('light-theme');
        body.classList.add('dark-theme');
        if (themeIcon) themeIcon.className = 'fas fa-sun';
    } else {
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        if (themeIcon) themeIcon.className = 'fas fa-moon';
    }
}

function toggleTheme() {
    const isDark = document.body.classList.contains('dark-theme');
    const newTheme = isDark ? 'light' : 'dark';
    localStorage.setItem('theme', newTheme);
    applyTheme(newTheme);
}

document.addEventListener('DOMContentLoaded', function() {
    // Apply saved theme or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
});