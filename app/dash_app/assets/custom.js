// app/dash_app/assets/custom.js

// Theme persistence via localStorage
(function() {
    const savedTheme = localStorage.getItem('crosswalk-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    window.setTheme = function(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('crosswalk-theme', theme);
    };
})();
