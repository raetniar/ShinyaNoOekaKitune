// Amazon Privacy Protector - Content Script

let currentSettings = { enabled: true, hideWishlist: true };

// 安全にChrome拡張のAPIを呼び出せるか判定する関数
function isExtensionValid() {
  try {
    return typeof chrome !== 'undefined' && chrome.runtime && !!chrome.runtime.id;
  } catch (e) {
    return false;
  }
}

// シールド状態（有効・無効）を読み込んでHTML属性を更新
function updateShieldState() {
  if (!isExtensionValid()) return;
  try {
    chrome.storage.local.get({ enabled: true, hideWishlist: true }, (result) => {
      if (!isExtensionValid() || chrome.runtime.lastError) return;
      currentSettings = result;

      if (result.enabled) {
        document.documentElement.setAttribute('data-amazon-privacy-shield', 'true');
      } else {
        document.documentElement.removeAttribute('data-amazon-privacy-shield');
      }

      if (result.enabled && result.hideWishlist) {
        document.documentElement.setAttribute('data-amazon-privacy-hide-wishlist', 'true');
      } else {
        document.documentElement.removeAttribute('data-amazon-privacy-hide-wishlist');
      }
    });
  } catch (e) {
    // コンテキスト無効化時の例外をキャッチ
  }
}

// 初期化時にシールド状態を反映
updateShieldState();

// ストレージ変更イベントを監視して動的にシールドを切り替え
if (isExtensionValid()) {
  try {
    chrome.storage.onChanged.addListener((changes, areaName) => {
      if (!isExtensionValid()) return;
      if (areaName === 'local' && (changes.enabled !== undefined || changes.hideWishlist !== undefined)) {
        updateShieldState();
      }
    });
  } catch (e) {
    // コンテキスト無効化時
  }
}

// 追加の動的ブロックロジック
const observer = new MutationObserver(() => {
  // 拡張機能がリロード/無効化された場合はObserverを停止しエラーを回避
  if (!isExtensionValid()) {
    observer.disconnect();
    return;
  }

  if (!currentSettings.enabled) return;

  // 1. 郵便番号「〒123-4567」および注文番号「250-1234567-8901234」形式のテキストを自動検知してぼかす
  const zipPattern = /〒\s?\d{3}-\d{4}/g;
  const orderIdPattern = /\b\d{3}-\d{7}-\d{7}\b/g;
  const targetTags = ['span', 'div', 'p', 'a', 'td', 'bdi', 'strong', 'b'];
  for (const tag of targetTags) {
    const elements = document.getElementsByTagName(tag);
    for (let i = 0; i < elements.length; i++) {
      const el = elements[i];
      if (el.classList.contains('amazon-privacy-masked')) continue;
      
      if (el.children.length === 0 && (zipPattern.test(el.textContent) || orderIdPattern.test(el.textContent))) {
        el.classList.add('amazon-privacy-masked');
      }
    }
  }

  // 2. 「受取人」「Eメールアドレス」「誕生日」「注文番号」「追跡番号」「お支払い方法」「クレジットカード」などの入力フォーム・ラベル領域を検出してぼかす
  const labels = document.querySelectorAll('label, .a-form-label, span.a-text-bold, span, div');
  const targetLabels = [
    '受取人', 'Eメールアドレス', '誕生日', 'Recipient', 'Email', 'Birthday',
    '注文番号', 'Order #', 'Order ID', '伝票番号', '追跡番号', 'Tracking Number',
    'クレジットカード', 'お支払い方法', 'Payment Method', '請求先住所'
  ];
  
  labels.forEach(label => {
    const text = label.textContent.trim();
    // 短いテキストでかつターゲットラベルが含まれる場合のみ処理
    if (text.length > 0 && text.length < 25 && targetLabels.some(t => text.includes(t))) {
      // ラベルの親要素（最大3階層上まで）からinput/select/spanを探してぼかす
      let parent = label.parentElement;
      for (let depth = 0; depth < 3; depth++) {
        if (!parent) break;
        const inputs = parent.querySelectorAll('input, select');
        inputs.forEach(input => {
          if (input.type !== 'submit' && input.type !== 'button' && input.type !== 'checkbox' && input.type !== 'radio') {
            if (!input.classList.contains('amazon-privacy-dynamic-masked')) {
              input.classList.add('amazon-privacy-dynamic-masked');
            }
          }
        });
        parent = parent.parentElement;
      }
    }
  });

  // 3. 欲しいものリスト・干し芋のリスト名・オーナー名の動的ぼかし (hideWishlistがONの場合のみ)
  if (currentSettings.hideWishlist) {
    const wishlistSelectors = [
      '#profile-wlp-name',
      '#profile-wlp-name *',
      '#profile-wlp-name-display',
      '#profile-wlp-name-display *',
      '[id*="wlp-name"]',
      '[id*="wlp-name"] *',
      '[id*="profile-wlp"]',
      '[id*="profile-wlp"] *',
      '[data-action*="wl-list"]',
      '[data-action*="wl-list"] *',
      'span[id^="profile-wlp-name"]',
      '#profile-name-text',
      '#al-intro-title',
      '#al-intro-title *',
      '#al-intro-title-text',
      '.al-intro-title',
      '.al-intro-title *',
      '#al-intro-description',
      '#profile-wlp-description',
      '.al-intro-description',
      '.g-story-title',
      '.al-intro-subtitle',
      '#al-intro-subtitle',
      '.g-party-name',
      '.g-profile-name',
      '#g-profile-name',
      '[id*="ListName"]',
      '[id^="ListName_"]',
      '[id^="ListName-"]',
      '#your-lists-nav .a-list-item',
      '#your-lists-nav a',
      '#al-your-lists .a-list-item',
      '#al-your-lists a',
      '#your-profile-nav .a-list-item',
      'a[href*="/hz/wishlist/ls/"]',
      'a[href*="/gp/registry/wishlist"]',
      '.wl-list-entry',
      '.wl-list-link',
      '.wl-list-item-title',
      '[id^="atwl-list-name"]',
      '.atwl-list-name',
      '#list-name',
      '#list-name-text',
      '#wl-list-title',
      '#nav-al-wishlist .nav-text'
    ];
    wishlistSelectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(el => {
        if (!el.classList.contains('amazon-privacy-wishlist-masked')) {
          el.classList.add('amazon-privacy-wishlist-masked');
        }
      });
    });
  }
});

// DOMの構築後に監視を開始
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    if (document.body) {
      observer.observe(document.body, { childList: true, subtree: true });
    }
  });
} else {
  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
  }
}
