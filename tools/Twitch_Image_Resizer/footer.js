/**
 * Common App Footer with AD Rotation Banner
 * Matches exact UI: [AD] 『ビデオサロン 2026年3月号』... | Twitchのフォローもお願いします！ | どねる
 */
(function() {
    // 1. Footer Styles Injection
    const styleId = 'common-footer-styles';
    if (!document.getElementById(styleId)) {
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            #common-app-footer {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                z-index: 9999;
                width: 100%;
                background-color: #121214;
                border-top: 1px solid #27272a;
                padding: 6px 16px;
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                font-size: 12px;
                color: #a1a1aa;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            body.light-mode #common-app-footer,
            body:not(.dark-mode) #common-app-footer {
                background-color: #f4f4f5;
                border-top-color: #e4e4e7;
                color: #71717a;
            }
            .global-ad-banner {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
                flex-wrap: nowrap;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 1200px;
                width: 100%;
            }
            .ad-badge {
                display: inline-block;
                background-color: #52525b;
                color: #ffffff;
                font-size: 10px;
                font-weight: 800;
                padding: 1px 5px;
                border-radius: 3px;
                line-height: 1.3;
                letter-spacing: 0.05em;
                flex-shrink: 0;
            }
            .ad-link {
                color: #efeff1;
                text-decoration: none;
                font-weight: 500;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                transition: color 0.2s;
            }
            body.light-mode .ad-link,
            body:not(.dark-mode) .ad-link {
                color: #18181b;
            }
            .ad-link:hover {
                color: #9146ff;
                text-decoration: underline;
            }
            .ad-divider {
                color: #3f3f46;
                font-size: 11px;
                flex-shrink: 0;
            }
            .twitch-link, .doneru-link {
                color: #a1a1aa;
                text-decoration: none;
                font-weight: 500;
                flex-shrink: 0;
                transition: color 0.2s;
            }
            body.light-mode .twitch-link,
            body.light-mode .doneru-link,
            body:not(.dark-mode) .twitch-link,
            body:not(.dark-mode) .doneru-link {
                color: #71717a;
            }
            .twitch-link:hover {
                color: #9146ff;
                text-decoration: underline;
            }
            .doneru-link:hover {
                color: #ef4444;
                text-decoration: underline;
            }
            body {
                padding-bottom: 38px !important;
            }
        `;
        document.head.appendChild(style);
    }

    const amazonAds = [
        { url: 'https://amzn.to/4tU7upp', text: '『ビデオサロン 2026年3月号』映像制作の最新情報をチェック...' },
        { url: 'https://amzn.to/4fF77Lx', text: '『デザインの基本ノート』レイアウト・配色に悩んだらコレ！' },
        { url: 'https://www.amazon.co.jp/cer/c/7e4fe727', text: 'AmazonプライムとTwitch連携で、好きな配信者に無料でサブスク！' },
        { url: 'https://amzn.to/4x1PegD', text: '『Blender完全ガイド』モデリングから質感・ライティングまで' },
        { url: 'https://amzn.to/4nIg0Gp', text: '『なるほどデザイン』目で見て楽しむデザインのコツ' },
        { url: 'https://amzn.to/43sgXsU', text: '『サムネイルデザインの教科書』クリックされるためのアイデア' },
        { url: 'https://amzn.to/3RDRIRQ', text: '『カラーパレット配色ブック』美しい配色の見本帳' },
        { url: 'https://amzn.to/4dqcKMs', text: '『はじめての3Dモデリング Blender実践入門』' },
        { url: 'https://amzn.to/4nFXw9o', text: '『ポーズと構図のデッサン集』魅力的なキャラを描く' },
        { url: 'https://amzn.to/4uqBUR5', text: '『デジタルイラストの「光と影」描き方事典』' },
        { url: 'https://amzn.to/4nLx2Uf', text: '『Photoshop & Illustrator 配色・デザインテクニック』' },
        { url: 'https://amzn.to/49QcGTR', text: '『背景の描き方マスターガイド』プロの現場の技' }
    ];

    function injectFooter() {
        if (document.getElementById('common-app-footer')) return;

        const footer = document.createElement('footer');
        footer.id = 'common-app-footer';
        
        footer.innerHTML = `
            <div class="global-ad-banner" id="ad-rotation-container" style="transition: opacity 0.5s ease-in-out; opacity: 1;">
                <span class="ad-badge">AD</span>
                <a id="amazon-ad-link" href="${amazonAds[0].url}" target="_blank" rel="noopener noreferrer" class="ad-link">
                    <span id="amazon-ad-text">${amazonAds[0].text}</span>
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

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectFooter);
    } else {
        injectFooter();
    }
})();
