// ─── Custom Cursor ───
var dot = document.createElement('div');
dot.className = 'cursor-dot';
document.body.appendChild(dot);

document.addEventListener('mousemove', function(e) {
  dot.style.left = e.clientX + 'px';
  dot.style.top = e.clientY + 'px';
});

document.addEventListener('mouseover', function(e) {
  var t = e.target.closest('a, button, .btn, .skill-tag, .hamburger, .theme-toggle');
  dot.classList.toggle('hover', !!t);
});

// ─── Scroll Reveal ───
const obs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('revealed');
      obs.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.skill-card, .edu-card, .proj-card, .exp-item, .stat-box, .contact-item').forEach(el => {
  obs.observe(el);
});

const hamburger = document.querySelector('.hamburger');
const navLinks = document.querySelector('.nav-links');
hamburger.addEventListener('click', () => {
  hamburger.classList.toggle('active');
  navLinks.classList.toggle('nav-active');
});
document.querySelectorAll('.nav-links a').forEach(link => {
  link.addEventListener('click', () => {
    hamburger.classList.remove('active');
    navLinks.classList.remove('nav-active');
  });
});

const themeToggle = document.getElementById('themeToggle');
const html = document.documentElement;
const savedTheme = localStorage.getItem('theme');

if (savedTheme) {
  html.setAttribute('data-theme', savedTheme);
  themeToggle.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
} else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
  html.setAttribute('data-theme', 'dark');
  themeToggle.textContent = '☀️';
}

themeToggle.addEventListener('click', () => {
  const current = html.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  themeToggle.textContent = next === 'dark' ? '☀️' : '🌙';
  localStorage.setItem('theme', next);
});
