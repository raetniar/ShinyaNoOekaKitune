// Screen Filter Pro - Popup Script

document.addEventListener('DOMContentLoaded', () => {
  const grayscaleSlider = document.getElementById('grayscaleSlider');
  const brightnessSlider = document.getElementById('brightnessSlider');
  
  const grayscaleValue = document.getElementById('grayscaleValue');
  const brightnessValue = document.getElementById('brightnessValue');
  
  const presetButtons = document.querySelectorAll('.btn-preset');

  // 初期値の読み込み (デフォルト: 白黒0%, 輝度100%)
  chrome.storage.local.get({ grayscale: 0, brightness: 100 }, (result) => {
    grayscaleSlider.value = result.grayscale;
    brightnessSlider.value = result.brightness;
    
    updateDisplayValues();
    highlightActivePreset(result.grayscale, result.brightness);
  });

  // スライダー操作イベントの登録
  grayscaleSlider.addEventListener('input', () => {
    saveSettings();
    updateDisplayValues();
  });

  brightnessSlider.addEventListener('input', () => {
    saveSettings();
    updateDisplayValues();
  });

  // プリセットボタンのクリックイベント
  presetButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const gray = parseInt(btn.getAttribute('data-gray'), 10);
      const bright = parseInt(btn.getAttribute('data-bright'), 10);

      grayscaleSlider.value = gray;
      brightnessSlider.value = bright;

      saveSettings();
      updateDisplayValues();
      highlightActivePreset(gray, bright);
    });
  });

  // 値の表示テキストを更新
  function updateDisplayValues() {
    grayscaleValue.textContent = `${grayscaleSlider.value}%`;
    brightnessValue.textContent = `${brightnessSlider.value}%`;
  }

  // 設定をストレージに保存
  function saveSettings() {
    const gray = parseInt(grayscaleSlider.value, 10);
    const bright = parseInt(brightnessSlider.value, 10);
    
    chrome.storage.local.set({ grayscale: gray, brightness: bright }, () => {
      highlightActivePreset(gray, bright);
    });
  }

  // アクティブなプリセットボタンを強調表示する処理
  function highlightActivePreset(gray, bright) {
    presetButtons.forEach(btn => {
      const bGray = parseInt(btn.getAttribute('data-gray'), 10);
      const bBright = parseInt(btn.getAttribute('data-bright'), 10);

      if (bGray === gray && bBright === bright) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }
});
