// APIベースURL
const API_BASE_URL = window.location.origin;

// DOM要素の取得
const tickerInput = document.getElementById('ticker-input');
const searchBtn = document.getElementById('search-btn');
const loading = document.getElementById('loading');
const errorMessage = document.getElementById('error-message');
const stockInfo = document.getElementById('stock-info');
const newsSection = document.getElementById('news-section');
const predictionSection = document.getElementById('prediction-section');

// イベントリスナーの設定
document.addEventListener('DOMContentLoaded', () => {
    // 検索ボタンのクリックイベント
    searchBtn.addEventListener('click', handleSearch);

    // Enterキーでの検索
    tickerInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });

    // 人気銘柄タグのクリックイベント
    const tickerTags = document.querySelectorAll('.ticker-tag');
    tickerTags.forEach(tag => {
        tag.addEventListener('click', () => {
            const ticker = tag.getAttribute('data-ticker');
            tickerInput.value = ticker;
            handleSearch();
        });
    });
});

// 検索処理
async function handleSearch() {
    const ticker = tickerInput.value.trim();

    if (!ticker) {
        showError('銘柄コードを入力してください');
        return;
    }

    // UIをリセット
    hideError();
    hideAllSections();
    showLoading();

    try {
        // 株価情報を取得
        const stockData = await fetchStockInfo(ticker);
        displayStockInfo(stockData);

        // ニュースを取得
        const newsData = await fetchNews(ticker);
        displayNews(newsData);

        // 予測を取得
        const predictionData = await fetchPrediction(ticker);
        displayPrediction(predictionData);

        hideLoading();
    } catch (error) {
        hideLoading();
        showError(error.message);
    }
}

// 株価情報を取得
async function fetchStockInfo(ticker) {
    const response = await fetch(`${API_BASE_URL}/api/stock/${ticker}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || '株価情報の取得に失敗しました');
    }
    return await response.json();
}

// ニュースを取得
async function fetchNews(ticker) {
    const response = await fetch(`${API_BASE_URL}/api/news/${ticker}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'ニュースの取得に失敗しました');
    }
    return await response.json();
}

// 予測を取得
async function fetchPrediction(ticker) {
    const response = await fetch(`${API_BASE_URL}/api/predict/${ticker}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || '予測の取得に失敗しました');
    }
    return await response.json();
}

// 株価情報を表示
function displayStockInfo(data) {
    // 銘柄名
    document.getElementById('stock-name').textContent =
        `${data.name} (${data.ticker})`;

    // 現在価格
    document.getElementById('current-price').textContent =
        formatCurrency(data.current_price, data.currency);

    // 価格変動
    const priceChange = document.getElementById('price-change');
    const changeAmount = document.getElementById('change-amount');
    const changePercent = document.getElementById('change-percent');

    if (data.change !== undefined) {
        const sign = data.change >= 0 ? '+' : '';
        changeAmount.textContent = `${sign}${formatCurrency(data.change, data.currency)}`;
        changePercent.textContent = `(${sign}${data.change_percent.toFixed(2)}%)`;

        // 色の設定
        priceChange.className = 'price-change ' + (data.change >= 0 ? 'positive' : 'negative');
    }

    // 最終更新時刻
    document.getElementById('last-updated').textContent =
        `最終更新: ${data.last_updated}`;

    // 詳細情報
    document.getElementById('open-price').textContent =
        formatCurrency(data.open, data.currency);
    document.getElementById('high-price').textContent =
        formatCurrency(data.high, data.currency);
    document.getElementById('low-price').textContent =
        formatCurrency(data.low, data.currency);
    document.getElementById('volume').textContent =
        formatNumber(data.volume);

    // その他の情報
    document.getElementById('market-cap').textContent =
        data.market_cap !== 'N/A' ? formatNumber(data.market_cap) : 'N/A';
    document.getElementById('pe-ratio').textContent =
        data.pe_ratio !== 'N/A' ? data.pe_ratio.toFixed(2) : 'N/A';
    document.getElementById('dividend-yield').textContent =
        data.dividend_yield !== 'N/A' ? (data.dividend_yield * 100).toFixed(2) + '%' : 'N/A';
    document.getElementById('week-52-high').textContent =
        data.week_52_high !== 'N/A' ? formatCurrency(data.week_52_high, data.currency) : 'N/A';
    document.getElementById('week-52-low').textContent =
        data.week_52_low !== 'N/A' ? formatCurrency(data.week_52_low, data.currency) : 'N/A';

    // セクションを表示
    stockInfo.classList.remove('hidden');
}

// ニュースを表示
function displayNews(data) {
    const newsContainer = document.getElementById('news-container');
    newsContainer.innerHTML = '';

    if (!data.news || data.news.length === 0) {
        newsContainer.innerHTML = '<p>ニュースが見つかりませんでした。</p>';
    } else {
        data.news.forEach(item => {
            const newsItem = document.createElement('div');
            newsItem.className = 'news-item';

            newsItem.innerHTML = `
                <h3><a href="${item.link}" target="_blank">${item.title}</a></h3>
                <div class="news-meta">
                    <span>📰 ${item.publisher}</span>
                    <span>📅 ${item.published}</span>
                </div>
                <p class="news-summary">${item.summary}</p>
            `;

            newsContainer.appendChild(newsItem);
        });
    }

    newsSection.classList.remove('hidden');
}

// 予測を表示
function displayPrediction(data) {
    // 予測価格
    document.getElementById('predicted-price').textContent =
        `¥${formatNumber(data.predicted_price)}`;

    // 予測変化
    const predictionChange = document.getElementById('prediction-change');
    const changePercent = document.getElementById('prediction-change-percent');

    const sign = data.predicted_change_percent >= 0 ? '+' : '';
    changePercent.textContent = `${sign}${data.predicted_change_percent.toFixed(2)}%`;

    // 色の設定
    predictionChange.className = 'prediction-change ' +
        (data.predicted_change_percent >= 0 ? 'positive' : 'negative');

    // 予測日
    document.getElementById('prediction-date').textContent =
        `予測日: ${data.prediction_date}`;

    // 信頼区間
    document.getElementById('confidence-upper').textContent =
        `¥${formatNumber(data.confidence_interval.upper)}`;
    document.getElementById('confidence-lower').textContent =
        `¥${formatNumber(data.confidence_interval.lower)}`;

    // テクニカル指標
    document.getElementById('ma-20').textContent =
        `¥${formatNumber(data.indicators.ma_20)}`;
    document.getElementById('ma-50').textContent =
        `¥${formatNumber(data.indicators.ma_50)}`;
    document.getElementById('volatility').textContent =
        `${data.indicators.volatility.toFixed(2)}%`;
    document.getElementById('trend').textContent =
        data.indicators.trend;

    // 分析結果
    document.getElementById('analysis-text').textContent =
        data.analysis;

    // 免責事項
    if (data.disclaimer) {
        document.getElementById('disclaimer-text').textContent =
            `⚠️ ${data.disclaimer}`;
    }

    // セクションを表示
    predictionSection.classList.remove('hidden');
}

// 通貨フォーマット
function formatCurrency(value, currency = 'JPY') {
    if (value === 'N/A' || value === null || value === undefined) {
        return 'N/A';
    }

    const num = parseFloat(value);
    if (isNaN(num)) {
        return 'N/A';
    }

    if (currency === 'JPY') {
        return `¥${num.toLocaleString('ja-JP', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        })}`;
    } else {
        return num.toLocaleString('ja-JP', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
}

// 数値フォーマット
function formatNumber(value) {
    if (value === 'N/A' || value === null || value === undefined) {
        return 'N/A';
    }

    const num = parseFloat(value);
    if (isNaN(num)) {
        return 'N/A';
    }

    if (num >= 1e12) {
        return (num / 1e12).toFixed(2) + '兆';
    } else if (num >= 1e8) {
        return (num / 1e8).toFixed(2) + '億';
    } else if (num >= 1e4) {
        return (num / 1e4).toFixed(2) + '万';
    } else {
        return num.toLocaleString('ja-JP', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        });
    }
}

// ローディング表示
function showLoading() {
    loading.classList.remove('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

// エラー表示
function showError(message) {
    errorMessage.textContent = `❌ ${message}`;
    errorMessage.classList.remove('hidden');
}

function hideError() {
    errorMessage.classList.add('hidden');
}

// すべてのセクションを非表示
function hideAllSections() {
    stockInfo.classList.add('hidden');
    newsSection.classList.add('hidden');
    predictionSection.classList.add('hidden');
}
