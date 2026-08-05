(function() {
    // 1. スタイルの動的注入
    const styleId = 'common-footer-styles';
    if (!document.getElementById(styleId)) {
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            :root {
                --common-footer-height: 38px;
            }
            .app-footer {
                padding: 6px 12px;
                border-top: 1px solid var(--border-color, #e5e7eb);
                background-color: var(--bg-panel, #ffffff);
                text-align: center;
                width: 100%;
                box-sizing: border-box;
                z-index: 10000;
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
                background-color: var(--bg-panel, #1e1e24);
                border-top-color: var(--border-color, #333338);
            }
            .global-ad-banner {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px 14px;
                flex-wrap: wrap;
                padding: 0 8px;
            }
            .ad-badge {
                background-color: #9146ff;
                color: #ffffff;
                font-size: 11px;
                font-weight: 800;
                padding: 2px 6px;
                border-radius: 4px;
                display: inline-block;
                flex-shrink: 0;
            }
            .ad-link {
                color: var(--text-primary, #111111);
                text-decoration: none;
                font-size: 12px;
                font-weight: 500;
                transition: color 0.2s;
                display: inline-flex;
                align-items: center;
                gap: 4px;
                max-width: 100%;
            }
            #amazon-ad-text {
                max-width: 360px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                display: inline-block;
                vertical-align: middle;
            }
            .ad-link:hover {
                color: #9146ff;
                text-decoration: underline;
            }
            .twitch-link {
                color: var(--text-secondary, #555555);
                text-decoration: none;
                font-size: 12px;
                font-weight: 600;
                transition: color 0.2s;
                white-space: nowrap;
            }
            .twitch-link:hover {
                color: #9146ff;
                text-decoration: underline;
            }
            .doneru-link {
                color: var(--text-primary, #111111) !important;
                text-decoration: none !important;
                font-size: 12px !important;
                font-weight: 600 !important;
                transition: color 0.2s;
                white-space: nowrap !important;
                background: none !important;
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
            }
            .doneru-link:hover {
                color: #9146ff !important;
                text-decoration: underline !important;
            }
            .ad-divider {
                margin: 0 2px;
                opacity: 0.4;
                color: var(--text-muted, #888888);
            }
            body.dark-mode .ad-link {
                color: var(--text-primary, #eeeeee);
            }
            body.dark-mode .twitch-link {
                color: var(--text-secondary, #cccccc);
            }
            body.dark-mode .doneru-link {
                color: var(--text-primary, #eeeeee) !important;
            }
            body.dark-mode .twitch-link:hover {
                color: #a970ff;
            }
            body.dark-mode .doneru-link:hover {
                color: #a970ff !important;
            }
            
            /* 重なり防止：ツール固有の固定フッターの底上げ */
            .sticky-footer-wrapper, .sticky-bottom-bar, .tab-content.active .sticky-footer-wrapper {
                bottom: var(--common-footer-height, 38px) !important;
            }

            @media (max-width: 768px) {
                #amazon-ad-text {
                    max-width: 220px;
                }
            }
            @media (max-width: 540px) {
                .ad-divider {
                    display: none;
                }
                #amazon-ad-text {
                    max-width: 160px;
                }
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

    function adjustFooterLayout() {
        const footerEl = document.getElementById('common-app-footer');
        if (!footerEl) return;
        const footerHeight = footerEl.offsetHeight || 38;
        document.documentElement.style.setProperty('--common-footer-height', footerHeight + 'px');
        
        // 独自固定操作バーのレイアウト調整（!important で底上げ）
        document.querySelectorAll('.sticky-footer-wrapper, .sticky-bottom-bar').forEach(el => {
            el.style.setProperty('bottom', footerHeight + 'px', 'important');
        });

        // bodyのpaddingBottomを設定
        document.body.style.paddingBottom = (footerHeight + 80) + 'px';
    }

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
                <span class="ad-divider">|</span>
                <a href="https://www.twitch.tv/uikouka" target="_blank" rel="noopener noreferrer" class="twitch-link">
                    Twitchのフォローもお願いします！
                </a>
                <span class="ad-divider">|</span>
                <a href="https://doneru.jp/uikouka" target="_blank" rel="noopener noreferrer" class="doneru-link">
                    どねる
                </a>
            </div>
        `;
        
        document.body.appendChild(footer);
        adjustFooterLayout();

        // 広告ローテーション開始
        initAdRotation();

        window.addEventListener('resize', adjustFooterLayout);
        setInterval(adjustFooterLayout, 1000);
        requestAnimationFrame(() => requestAnimationFrame(adjustFooterLayout));
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
                adjustFooterLayout();
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
  var _script = document.currentScript;

  function insertWarning() {
    var showWarning = _script && _script.getAttribute('data-show-warning') === 'true';
    if (!showWarning) return;

    if (document.getElementById('tool-warning-banner')) return;

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

    var warningDiv = document.createElement('div');
    warningDiv.id = 'tool-warning-banner';
    warningDiv.textContent = '当サイト上のツールは、データを取得することはありませんが動作確認用にのみ使用し、個人情報は記載しないようにお願いいたします。ツール自体はBoothにて無料配布して居ります';
    document.body.insertBefore(warningDiv, document.body.firstChild);

    function adjustHeaderTop() {
      var banner = document.getElementById('tool-warning-banner');
      var header = document.querySelector('.tool-header-bar');
      if (!banner || !header) return;
      var bannerH = banner.offsetHeight;
      header.style.top = bannerH + 'px';
    }

    requestAnimationFrame(function() {
      requestAnimationFrame(adjustHeaderTop);
    });

    window.addEventListener('resize', adjustHeaderTop);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', insertWarning);
  } else {
    insertWarning();
  }
})();
