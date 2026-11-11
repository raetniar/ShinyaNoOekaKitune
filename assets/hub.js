const themeButton = document.getElementById('theme');
const themeIcons = {
  dark: '<svg class="theme-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M20.2 15.7A8.6 8.6 0 0 1 8.3 3.8 8.8 8.8 0 1 0 20.2 15.7Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  light: '<svg class="theme-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.8"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.5 1.5m11.2 11.2 1.5 1.5m0-14.2-1.5 1.5M6.4 17.6l-1.5 1.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
};
function setTheme(value) {
  document.documentElement.dataset.theme = value;
  if (!themeButton) return;
  themeButton.innerHTML = themeIcons[value === 'light' ? 'light' : 'dark'];
  const label = value === 'light' ? '暗い配色に切り替える' : '明るい配色に切り替える';
  themeButton.setAttribute('aria-label', label);
  themeButton.title = label;
}
let storedTheme;
try { storedTheme = localStorage.getItem('uikouka-hub-theme'); } catch {}
setTheme(storedTheme === 'light' ? 'light' : 'dark');
if (themeButton) {
  themeButton.hidden = false;
  themeButton.addEventListener('click', () => {
    const value = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
    setTheme(value);
    try { localStorage.setItem('uikouka-hub-theme', value); } catch {}
  });
}// Pick one approved recommendation per category on each page load.
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
    const selectedUrl = new URL(chosen.url);
    const videoId = selectedUrl.hostname === 'youtu.be' ? selectedUrl.pathname.slice(1) :
      (selectedUrl.pathname.startsWith('/shorts/') ? selectedUrl.pathname.split('/')[2] : selectedUrl.searchParams.get('v'));
    const image = card.querySelector('.recommendation-image') || document.createElement('img');
    image.className = 'recommendation-image';
    image.src = `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`;
    image.alt = '';
    image.loading = 'lazy';
    image.width = 480;
    image.height = 360;
    image.onerror = () => image.remove();
    if (!image.parentNode) card.prepend(image);
    if (chosen.title) card.querySelector('h3').textContent = chosen.title;
  }
}
applyRecommendations(window.UIKO_RECOMMENDATIONS);

// Show the same descriptions on hover, keyboard focus and the touch info button.
const socialRail = document.querySelector('.social-rail');
const socialTooltip = document.getElementById('social-tooltip');
if (socialRail?.querySelectorAll && socialTooltip?.style) {
  function hideSocialTooltip() {
    socialTooltip.hidden = true;
    socialRail.querySelectorAll('.social-info').forEach(button => button.setAttribute('aria-expanded', 'false'));
  }
  function showSocialTooltip(item) {
    const name = item.querySelector('.social-link-item > span').textContent.trim();
    const description = item.querySelector('.social-description').textContent.trim();
    socialTooltip.textContent = name === description ? name : `${name}：${description}`;
    socialTooltip.hidden = false;
    const rect = item.getBoundingClientRect();
    const box = socialTooltip.getBoundingClientRect();
    const left = Math.max(12, Math.min(rect.left, window.innerWidth - box.width - 12));
    const top = rect.bottom + box.height + 20 < window.innerHeight ? rect.bottom + 8 : Math.max(12, rect.top - box.height - 8);
    socialTooltip.style.left = `${left}px`;
    socialTooltip.style.top = `${top}px`;
  }
  socialRail.querySelectorAll('.social-item').forEach(item => {
    item.addEventListener('pointerenter', event => {
      if (event.pointerType !== 'touch') showSocialTooltip(item);
    });
    item.addEventListener('pointerleave', () => {
      if (!item.matches(':focus-within')) hideSocialTooltip();
    });
    item.addEventListener('focusin', () => showSocialTooltip(item));
    item.addEventListener('focusout', event => {
      if (!item.contains(event.relatedTarget)) hideSocialTooltip();
    });
    item.querySelector('.social-info').addEventListener('click', event => {
      const button = event.currentTarget;
      const expanded = button.getAttribute('aria-expanded') === 'true';
      hideSocialTooltip();
      if (!expanded) {
        showSocialTooltip(item);
        button.setAttribute('aria-expanded', 'true');
      }
    });
  });
  document.addEventListener('click', event => {
    if (!socialRail.contains(event.target)) hideSocialTooltip();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') hideSocialTooltip();
  });
  document.addEventListener('scroll', hideSocialTooltip, true);
  window.addEventListener('resize', hideSocialTooltip);
}
