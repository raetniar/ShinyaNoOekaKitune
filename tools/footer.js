(function() {
    // 1. スタイルの動的注入
    const styleId = 'common-footer-styles';
    if (!document.getElementById(styleId)) {
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .app-footer {
                padding: 12px 0;
                border-top: 1px solid var(--border-color, #e5e7eb);
                background-color: var(--bg-panel, #ffffff);
                text-align: center;
                width: 100%;
                box-sizing: border-box;
                z-index: 1000;
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
            }
            body.light-mode .app-footer {
                background-color: var(--bg-panel, #ffffff);
                border-top-color: var(--border-color, #e5e7eb);
            }
            body.dark-mode .app-footer {
                background-color: var(--bg-panel, #222222);
                border-top-color: var(--border-color, #333333);
            }
            .global-ad-banner {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                flex-wrap: wrap;
                padding: 0 15px;
            }
            .ad-badge {
                background-color: #9146ff;
                color: #ffffff;
                font-size: 11px;
                font-weight: 800;
                padding: 2px 6px;
                border-radius: 4px;
                display: inline-block;
            }
            .ad-link {
                color: var(--text-primary, #111111);
                text-decoration: none;
                font-size: 13px;
                font-weight: 500;
                transition: color 0.2s;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }
            .ad-link:hover {
                color: #9146ff;
                text-decoration: underline;
            }
            .twitch-link {
                color: var(--text-secondary, #555555);
                text-decoration: none;
                font-size: 13px;
                font-weight: 500;
                transition: color 0.2s;
            }
            .twitch-link:hover {
                color: #9146ff;
                text-decoration: underline;
            }
        `;
        document.head.appendChild(style);
    }

    // 広告データ
    const amazonAds = [
        { url: 'https://www.amazon.co.jp/cer/c/7e4fe727', text: 'AmazonプライムとTwitchを連携すると、お好きな配信者に毎月無料でサブスク（支援）ができます！' },
        { url: 'https://amzn.to/4x1PegD', text: '『Blender完全入門』形から質感、光、撮影まで全部できる！' },
        { url: 'https://amzn.to/4tU7upp', text: '『ビデオサロン 2026年3月号』映像制作の最新情報をチェック' },
        { url: 'https://amzn.to/4nIg0Gp', text: '『なるほどデッサン』みるみる上達するコツ教えます' },
        { url: 'https://amzn.to/43sgXsU', text: '『サムネイルデザインのきほん』伝える、目立たせるためのアイデア' },
        { url: 'https://amzn.to/3RDRIRQ', text: '『「悩まない」配色の基本』好きな色から考えるデザイン' },
        { url: 'https://amzn.to/4dqcKMs', text: '『はじめての3Dモデリング Blender 4 超入門』' },
        { url: 'https://amzn.to/4nFXw9o', text: '『大人のデッサン・お絵描き入門』楽しく描いて上手くなる' },
        { url: 'https://amzn.to/4uqBUR5', text: '『デジタルイラストの「ポーズ」見ちがえる描き方図鑑』' },
        { url: 'https://amzn.to/4nLx2Uf', text: '『Photoshop＆Illustrator デザインテクニック大全』' },
        { url: 'https://amzn.to/49QcGTR', text: '『背景の描き方 決定版』魅力的な背景を描くためのコツ' }
    ];

    // 2. フッターの生成と挿入
    function injectFooter() {
        if (document.getElementById('common-app-footer')) return;

        const footer = document.createElement('footer');
        footer.id = 'common-app-footer';
        footer.className = 'app-footer';
        
        footer.innerHTML = `
            <div class="global-ad-banner" id="ad-rotation-container" style="transition: opacity 0.5s ease-in-out; opacity: 1;">
                <a id="amazon-ad-link" href="#" target="_blank" rel="noopener noreferrer" class="ad-link">
                    <span class="ad-badge">AD</span><span id="amazon-ad-text">読み込み中...</span>
                </a>
                <span style="margin: 0 10px; opacity: 0.5; color: var(--text-muted, #888888);">|</span>
                <a href="https://www.twitch.tv/uikouka" target="_blank" rel="noopener noreferrer" class="twitch-link">
                    Twitchのフォローもお願いします！
                </a>
            </div>
        `;
        
        // bodyのpaddingBottomを設定して、フッターがコンテンツに重ならないようにする
        document.body.style.paddingBottom = '60px';
        document.body.appendChild(footer);

        // 広告ローテーション開始
        initAdRotation();
    }

    function initAdRotation() {
        const adContainer = document.getElementById('ad-rotation-container');
        const adAnchor = document.getElementById('amazon-ad-link');
        const adText = document.getElementById('amazon-ad-text');
        if (!adContainer || !adAnchor || !adText) return;

        let currentIndex = Math.floor(Math.random() * amazonAds.length);
        adAnchor.href = amazonAds[currentIndex].url;
        adText.textContent = amazonAds[currentIndex].text;

        setInterval(() => {
            adContainer.style.opacity = '0';
            setTimeout(() => {
                currentIndex = (currentIndex + 1) % amazonAds.length;
                adAnchor.href = amazonAds[currentIndex].url;
                adText.textContent = amazonAds[currentIndex].text;
                adContainer.style.opacity = '1';
            }, 500);
        }, 8000);
    }

    // ページの読み込み完了時に注入
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectFooter);
    } else {
        injectFooter();
    }
})();

// === Warning injection based on script attribute ===
(function() {
  // currentScript は実行時に即キャプチャ（コールバック内では null になるため）
  var _script = document.currentScript;

  function insertWarning() {
    // フラグ確認
    var showWarning = _script && _script.getAttribute('data-show-warning') === 'true';
    if (!showWarning) return;

    // 重複挿入防止
    if (document.getElementById('tool-warning-banner')) return;

    // --- スタイル注入 ---
    var styleId = 'common-warning-styles';
    if (!document.getElementById(styleId)) {
      var style = document.createElement('style');
      style.id = styleId;
      style.textContent = [
        '#tool-warning-banner {',
        '  position: fixed;',
        '  top: 0;',
        '  left: 0;',
        '  right: 0;',
        '  z-index: 10001;',
        '  box-sizing: border-box;',
        '  width: 100%;',
        '  background: rgba(255,251,200,0.97);',
        '  color: #3d3000;',
        '  font-size: clamp(0.65rem, 1.2vw, 0.78rem);',
        '  font-weight: 500;',
        '  padding: 5px 16px;',
        '  text-align: center;',
        '  border-bottom: 1px solid rgba(200,180,0,0.5);',
        '  letter-spacing: 0.01em;',
        '  line-height: 1.5;',
        '  white-space: normal;',
        '  word-break: break-all;',
        '  overflow-wrap: break-word;',
        '}',
        'body.dark-mode #tool-warning-banner {',
        '  background: rgba(50,45,10,0.97);',
        '  color: #e8d87a;',
        '  border-bottom-color: rgba(180,160,0,0.5);',
        '}'
      ].join('\n');
      document.head.appendChild(style);
    }

    // --- バナー要素作成・挿入 ---
    var warningDiv = document.createElement('div');
    warningDiv.id = 'tool-warning-banner';
    warningDiv.textContent = '当サイト上のツールは、データを取得することはありませんが動作確認用にのみ使用し、個人情報は記載しないようにお願いいたします。ツール自体はBoothにて無料配布して居ります';
    // body の先頭に fixed で追加
    document.body.insertBefore(warningDiv, document.body.firstChild);

    // --- tool-header-bar の top をバナー高さ分ずらす ---
    function adjustHeaderTop() {
      var banner = document.getElementById('tool-warning-banner');
      var header = document.querySelector('.tool-header-bar');
      if (!banner || !header) return;
      var bannerH = banner.offsetHeight;
      header.style.top = bannerH + 'px';
    }

    // 描画確定後に初回調整（offsetHeight がレイアウト後に確定するため rAF 2重がけ）
    requestAnimationFrame(function() {
      requestAnimationFrame(adjustHeaderTop);
    });

    // ウィンドウリサイズ時にも再調整
    window.addEventListener('resize', adjustHeaderTop);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', insertWarning);
  } else {
    insertWarning();
  }
})();
