// static/js/theme.js
// Centralized theme toggle logic for QuizPro
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('themeToggle');
  const root = document.documentElement;
  // Apply saved theme preference and set toggle state
  const currentTheme = localStorage.getItem('theme') || 'light';
  if (currentTheme === 'dark') {
    root.classList.add('dark');
  }
  if (toggle && toggle.type === 'checkbox') {
    toggle.checked = (currentTheme === 'dark');
  }
  if (!toggle) return;
  // Toggle theme based on checkbox change
  toggle.addEventListener('change', () => {
    if (toggle.checked) {
      root.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      root.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  });
}); 