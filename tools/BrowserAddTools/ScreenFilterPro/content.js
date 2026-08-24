// Screen Filter Pro - Content Script

// ストレージから設定値を読み込み、動的な<style>タグを生成・更新して適用する関数
function applyFilters() {
  chrome.storage.local.get({ grayscale: 0, brightness: 100 }, (result) => {
    if (document.documentElement) {
      const styleId = 'screen-filter-pro-dynamic-style';
      let styleEl = document.getElementById(styleId);
      
      if (!styleEl) {
        styleEl = document.createElement('style');
        styleEl.id = styleId;
        (document.head || document.documentElement).appendChild(styleEl);
      }
      
      styleEl.textContent = `
        html {
          filter: grayscale(${result.grayscale}%) brightness(${result.brightness}%) !important;
        }
      `;
    }
  });
}

// 初期化時にフィルタを即時反映（FOUC防ぐためdocument_startで即時実行）
applyFilters();

// DOMが作成されたタイミングでも再適用
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', applyFilters);
} else {
  applyFilters();
}

// ユーザーがポップアップでスライダーを変更した際にリアルタイム反映するための監視
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === 'local') {
    if (changes.grayscale !== undefined || changes.brightness !== undefined) {
      applyFilters();
    }
  }
});
