// static/js/theme.js
// Centralized theme toggle logic for QuizPro
document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('themeToggle');
  const root = document.documentElement;
  // Apply saved theme preference
  const currentTheme = localStorage.getItem('theme') || 'light';
  if (currentTheme === 'dark') {
    root.classList.add('dark');
  }
  if (!toggleBtn) return;
  // Toggle theme on button click
  toggleBtn.addEventListener('click', () => {
    const isDark = root.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  });
}); 