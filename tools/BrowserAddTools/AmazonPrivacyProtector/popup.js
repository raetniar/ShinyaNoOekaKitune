// Amazon Privacy Protector - Popup Script

document.addEventListener('DOMContentLoaded', () => {
  const shieldToggle = document.getElementById('shieldToggle');
  const wishlistToggle = document.getElementById('wishlistToggle');
  const wishlistControlRow = document.getElementById('wishlistControlRow');
  const wishlistFeatureItem = document.getElementById('wishlistFeatureItem');
  const statusCard = document.getElementById('statusCard');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const statusDesc = document.getElementById('statusDesc');
  const shieldSvg = document.getElementById('shieldSvg');

  // 初期値の読み込み (デフォルト: enabled=true, hideWishlist=true)
  chrome.storage.local.get({ enabled: true, hideWishlist: true }, (result) => {
    shieldToggle.checked = result.enabled;
    wishlistToggle.checked = result.hideWishlist;
    updateUI(result.enabled, result.hideWishlist);
  });

  // メイントグル変更の監視
  shieldToggle.addEventListener('change', () => {
    const isEnabled = shieldToggle.checked;
    chrome.storage.local.set({ enabled: isEnabled }, () => {
      updateUI(isEnabled, wishlistToggle.checked);
    });
  });

  // 干し芋リスト（欲しいものリスト）トグル変更の監視
  wishlistToggle.addEventListener('change', () => {
    const isWishlistHide = wishlistToggle.checked;
    chrome.storage.local.set({ hideWishlist: isWishlistHide }, () => {
      updateUI(shieldToggle.checked, isWishlistHide);
    });
  });

  // UI表示の更新処理
  function updateUI(enabled, hideWishlist) {
    if (enabled) {
      statusCard.classList.add('active');
      shieldSvg.classList.remove('disabled');
      wishlistControlRow.classList.remove('disabled');
      wishlistToggle.disabled = false;
      statusText.textContent = '保護有効';

      if (hideWishlist) {
        statusDesc.textContent = '住所、氏名、注文番号、追跡番号、カード情報、欲しいものリスト等を全自動で隠しています';
        wishlistFeatureItem.style.opacity = '1';
      } else {
        statusDesc.textContent = '住所、氏名、注文番号、追跡番号、カード情報などの個人情報を隠しています';
        wishlistFeatureItem.style.opacity = '0.35';
      }
    } else {
      statusCard.classList.remove('active');
      shieldSvg.classList.add('disabled');
      wishlistControlRow.classList.add('disabled');
      wishlistToggle.disabled = true;
      statusText.textContent = '保護無効';
      statusDesc.textContent = '個人情報の保護機能がオフになっています（一時停止中）';
    }
  }
});
