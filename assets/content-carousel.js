// Lightweight recommendation carousels. Video playback stays on YouTube.
(() => {
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  for (const category of ['shorts', 'videos']) {
    const original = document.querySelector(`[data-recommendation="${category}"]`);
    if (!original) continue;
    const seen = new Set();
    const candidates = (window.UIKO_RECOMMENDATIONS?.[category] || []).flatMap(item => {
      const url = recommendationUrl(typeof item === 'string' ? item : item?.url, category);
      if (!url) return [];
      const parsed = new URL(url);
      const id = parsed.hostname === 'youtu.be' ? parsed.pathname.slice(1) :
        parsed.pathname.startsWith('/shorts/') ? parsed.pathname.split('/')[2] : parsed.searchParams.get('v');
      if (seen.has(id)) return [];
      seen.add(id);
      return [{url, id}];
    });
    if (!candidates.length) continue;
    for (let i = candidates.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
    }
    const shell = document.createElement('div');
    shell.className = 'recommendation-carousel';
    shell.setAttribute('role', 'group');
    shell.setAttribute('aria-label', category === 'shorts' ? 'Shorts' : '動画');
    const viewport = document.createElement('div');
    viewport.className = 'carousel-viewport';
    const track = document.createElement('div');
    track.className = 'carousel-track';
    const multiple = candidates.length > 1;
    const slides = multiple ? [candidates.at(-1), ...candidates, candidates[0]] : candidates;
    for (const entry of slides) {
      const slide = original.cloneNode(true);
      slide.removeAttribute('data-recommendation');
      slide.href = entry.url;
      slide.draggable = false;
      let image = slide.querySelector('.recommendation-image');
      if (!image) { image = document.createElement('img'); slide.prepend(image); }
      Object.assign(image, {className:'recommendation-image', src:`https://i.ytimg.com/vi/${entry.id}/hqdefault.jpg`, alt:'', loading:'lazy', width:480, height:360, draggable:false});
      image.addEventListener('error', () => { image.style.visibility = 'hidden'; });
      track.append(slide);
    }
    viewport.append(track);
    shell.append(viewport);
    original.replaceWith(shell);
    let position = multiple ? 1 : 0;
    let busy = false, timer, settleTimer, hovering = false, focused = false, visible = true;
    let paused = reducedMotion.matches;
    let controlsOpen = false, revealTimer, lastTouchAt = 0;
    function hideControls() {
      controlsOpen = false; shell.classList.remove('controls-open'); clearTimeout(revealTimer); schedule();
    }
    function revealControls() {
      controlsOpen = true; shell.classList.add('controls-open'); clearTimeout(revealTimer);
      revealTimer = setTimeout(hideControls, 4000); schedule();
    }
    const controls = document.createElement('div');
    controls.className = 'carousel-controls';
    const makeButton = (label, symbol) => {
      const button = document.createElement('button');
      button.type = 'button'; button.setAttribute('aria-label', label);
      const icon = document.createElement('span'); icon.setAttribute('aria-hidden', 'true'); icon.textContent = symbol;
      button.append(icon); return button;
    };
    const previous = makeButton('前の動画', '‹');
    const next = makeButton('次の動画', '›');
    const toggle = makeButton('自動切り替えを一時停止', 'Ⅱ');
    const count = document.createElement('span'); count.className = 'carousel-count';
    controls.append(previous, count, next, toggle);
    if (multiple) shell.append(controls);
    const logicalIndex = () => ((position - 1 + candidates.length) % candidates.length);
    function paint(animate = true) {
      const transferFocus = track.contains(document.activeElement);
      track.style.transition = animate && !reducedMotion.matches ? '' : 'none';
      track.style.transform = `translateX(-${position * 100}%)`;
      [...track.children].forEach((slide, i) => {
        slide.inert = i !== position;
        slide.setAttribute('aria-hidden', i === position ? 'false' : 'true');
      });
      count.textContent = `${logicalIndex() + 1} / ${candidates.length}`;
      if (transferFocus) track.children[position].focus({preventScroll:true});
    }
    function syncToggle() {
      toggle.setAttribute('aria-label', paused ? '自動切り替えを再開' : '自動切り替えを一時停止');
      toggle.firstElementChild.textContent = paused ? '▶' : 'Ⅱ';
    }
    function schedule() {
      clearTimeout(timer);
      if (multiple && !paused && !controlsOpen && !hovering && !focused && visible && !document.hidden) timer = setTimeout(() => move(1), 10000);
    }
    function settle() {
      clearTimeout(settleTimer);
      if (position === 0) position = candidates.length;
      else if (position === candidates.length + 1) position = 1;
      paint(false); busy = false;
    }
    function move(direction) {
      if (!multiple || busy) return;
      busy = true;
      // Commit the resting transform before enabling the next transition.
      track.getBoundingClientRect();
      position += direction;
      paint();
      settleTimer = setTimeout(settle, reducedMotion.matches ? 0 : 500);
      schedule();
    }
    previous.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    toggle.addEventListener('click', () => { paused = !paused; syncToggle(); schedule(); });
    shell.addEventListener('pointerenter', event => { if (event.pointerType === 'mouse') { hovering = true; schedule(); } });
    shell.addEventListener('pointerleave', () => { hovering = false; schedule(); });
    shell.addEventListener('focusin', () => { focused = true; schedule(); });
    shell.addEventListener('focusout', event => { if (!shell.contains(event.relatedTarget)) { focused = false; schedule(); } });
    shell.addEventListener('keydown', event => {
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); move(event.key === 'ArrowLeft' ? -1 : 1); }
    });
    let touchStart, suppressClick = false;
    viewport.addEventListener('touchstart', event => {
      lastTouchAt = Date.now();
      if (event.touches.length === 1) touchStart = {x:event.touches[0].clientX, y:event.touches[0].clientY};
      clearTimeout(timer);
    }, {passive:true});
    viewport.addEventListener('touchend', event => {
      if (touchStart && event.changedTouches.length) {
        const dx = event.changedTouches[0].clientX - touchStart.x;
        const dy = event.changedTouches[0].clientY - touchStart.y;
        if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.3) { suppressClick = true; move(dx < 0 ? 1 : -1); setTimeout(() => { suppressClick = false; }, 400); }
      }
      touchStart = null; schedule();
    }, {passive:true});
    viewport.addEventListener('touchcancel', () => { touchStart = null; schedule(); }, {passive:true});
    viewport.addEventListener('click', event => {
      if (suppressClick) { event.preventDefault(); event.stopPropagation(); suppressClick = false; return; }
      if (event.pointerType !== 'touch' && Date.now() - lastTouchAt > 700) return;
      const image = track.children[position].querySelector('.recommendation-image');
      const rect = image.getBoundingClientRect();
      const onImage = event.clientX >= rect.left && event.clientX <= rect.right && event.clientY >= rect.top && event.clientY <= rect.bottom;
      if (onImage && !controlsOpen) { event.preventDefault(); event.stopPropagation(); revealControls(); }
    }, true);
    controls.addEventListener('pointerdown', event => { if (event.pointerType === 'touch') revealControls(); });
    document.addEventListener('pointerdown', event => { if (!shell.contains(event.target) && controlsOpen) hideControls(); });
    document.addEventListener('visibilitychange', schedule);
    if ('IntersectionObserver' in window) new IntersectionObserver(entries => { visible = entries[0].isIntersecting; schedule(); }, {threshold:0.1}).observe(shell);
    reducedMotion.addEventListener('change', () => { if (reducedMotion.matches) paused = true; syncToggle(); schedule(); });
    paint(false); syncToggle(); schedule();
  }
})();

