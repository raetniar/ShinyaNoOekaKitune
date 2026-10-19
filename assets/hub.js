const themeButton = document.getElementById('theme');
function setTheme(value) {
  document.documentElement.dataset.theme = value;
  themeButton.textContent = value === 'light' ? '配色：昼' : '配色：夜';
  themeButton.setAttribute('aria-label', value === 'light' ? '暗い配色に切り替える' : '明るい配色に切り替える');
}
let storedTheme;
try { storedTheme = localStorage.getItem('uikouka-hub-theme'); } catch {}
setTheme(storedTheme === 'light' ? 'light' : 'dark');
themeButton.hidden = false;
themeButton.addEventListener('click', () => {
  const value = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
  setTheme(value);
  try { localStorage.setItem('uikouka-hub-theme', value); } catch {}
});
