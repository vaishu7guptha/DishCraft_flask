// theme.js
const toggle = document.getElementById('theme-toggle');

// initialize based on saved preference
if (localStorage.getItem('theme') === 'dark') {
  document.body.classList.add('dark-mode');
  toggle.checked = true;
}

toggle.addEventListener('change', () => {
  if (toggle.checked) {
    document.body.classList.add('dark-mode');
    localStorage.setItem('theme', 'dark');
  } else {
    document.body.classList.remove('dark-mode');
    localStorage.setItem('theme', 'light');
  }
});
