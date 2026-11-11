/* Site-wide links resolve from the GitHub Pages project root. */
(() => {
 const root = new URL('../', document.currentScript.src);
 const link = value => new URL(value, root).href;
 const path = decodeURIComponent(location.pathname.slice(root.pathname.length)) || 'index.html';
 const home = path === 'index.html';
 const guide = path === 'creator-guide.html';
 const record = path === 'omikuji.html';
 const privacy = path === 'privacy.html';
 const collection = path === 'tools.html' || path === 'tools/index.html';
 const tool = path.startsWith('tools/') && !collection;
 const test = path.startsWith('TestPage/');
 const title = guide ? '作品とツールの案内' : record ? 'おみくじ企画の記録' : privacy ? 'プライバシーポリシー' : collection ? 'ツール一覧' : (document.querySelector('h1')?.textContent.trim().slice(0,70) || document.title.split(/[|｜]/)[0] || 'ツール');
 const entries = [['HOME','index.html',home],['LIVE','index.html#live',false],['WORKS','index.html#works',false],['TOOLS','tools.html',collection || tool],['GUIDE','creator-guide.html',guide],['LINKS','index.html#links',false]];
 function a(label, target, active=false) {
  const el=document.createElement('a');el.href=link(target);el.textContent=label;
  if(active)el.setAttribute('aria-current','page');
  return el;
 }
 function menu() {
  const n=document.createElement('nav');n.className='site-unified-menu';
  n.setAttribute('aria-label','サイト共通メニュー');
  for(const [name,target,active] of entries)n.appendChild(a(name,target,active));
  return n;
 }
 function crumbs() {
  const n=document.createElement('nav');n.className='site-unified-crumbs';
  n.setAttribute('aria-label','現在地');
  const steps=[['ホーム','index.html']];
  if(tool)steps.push(['ツール一覧','tools.html']);
  steps.push([title,null]);
  steps.forEach(([name,target],i)=>{
   if(i){const s=document.createElement('span');s.textContent='›';s.setAttribute('aria-hidden','true');n.appendChild(s);}
   if(target)n.appendChild(a(name,target));
   else{const s=document.createElement('span');s.textContent=name;s.setAttribute('aria-current','page');n.appendChild(s);}
  });
  return n;
 }
 const existing=document.querySelector('.site-header nav[aria-label="メインナビゲーション"]');
 if(existing){
  const n=menu();existing.replaceChildren(...n.children);
  existing.classList.add('site-unified-menu');
  existing.setAttribute('aria-label','サイト共通メニュー');
  if(!home)document.querySelector('.site-header').insertAdjacentElement('afterend',crumbs());
 }else{
  const bar=document.createElement('div');bar.className='site-unified-bar';
  const row=document.createElement('div');row.className='site-unified-row';
  const brand=a('初狐羽鹿 / HOME','index.html');brand.className='site-unified-brand';
  row.append(brand,menu());bar.appendChild(row);
  if(!home)bar.appendChild(crumbs());
  if(tool || test){
   const back=a('‹ ツール一覧へ戻る','tools.html');back.className='site-unified-back';bar.appendChild(back);
  }
  document.body.insertAdjacentElement('afterbegin',bar);
 }
})();
