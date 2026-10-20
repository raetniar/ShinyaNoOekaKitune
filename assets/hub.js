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

// Pick one approved recommendation per category on each page load.
function recommendationUrl(value, category) {
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.username || url.password) return null;
    const youtube = ['youtube.com', 'www.youtube.com', 'm.youtube.com'].includes(url.hostname);
    const shortHost = url.hostname === 'youtu.be';
    const shortId = youtube && /^\/shorts\/[A-Za-z0-9_-]{11}\/?$/.test(url.pathname);
    const videoId = (youtube && url.pathname === '/watch' && /^[A-Za-z0-9_-]{11}$/.test(url.searchParams.get('v') || '')) ||
      (shortHost && /^\/[A-Za-z0-9_-]{11}\/?$/.test(url.pathname));
    return ((category === 'shorts' && shortId) || (category === 'videos' && videoId)) ? url.href : null;
  } catch { return null; }
}
function applyRecommendations(config, random = Math.random) {
  for (const category of ['shorts', 'videos']) {
    const supplied = config?.[category];
    const candidates = Array.isArray(supplied) ? supplied.map(item => {
      const url = recommendationUrl(typeof item === 'string' ? item : item?.url, category);
      return url ? {url, title: typeof item?.title === 'string' ? item.title.trim() : ''} : null;
    }).filter(Boolean) : [];
    if (!candidates.length) continue;
    const card = document.querySelector(`[data-recommendation="${category}"]`);
    if (!card) continue;
    const chosen = candidates[Math.floor(random() * candidates.length)];
    card.href = chosen.url;
    if (chosen.title) card.querySelector('h3').textContent = chosen.title;
  }
}
applyRecommendations(window.UIKO_RECOMMENDATIONS);
