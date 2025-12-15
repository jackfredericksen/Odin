/**
 * Odin Analytics Dashboard - Modern Bitcoin Market Intelligence
 * REAL DATA ONLY - Connects to trusted APIs
 */

class AnalyticsDashboard {
    constructor() {
        this.apiBase = '/api/v1';
        this.charts = {};
        this.updateInterval = 30000; // 30 seconds
        this.intervals = [];
        this.currentPrice = 0;

        this.init();
    }

    async init() {
        console.log('🚀 Initializing Odin Analytics Dashboard - Real Data Only');

        // Start clock
        this.startClock();

        // Load REAL data from APIs
        await this.loadAllData();

        // Initialize charts
        this.initializeCharts();

        // Start auto-update
        this.startAutoUpdate();

        console.log('✅ Dashboard initialized with real data feeds');
    }

    startClock() {
        const updateClock = () => {
            const now = new Date();
            const timeString = now.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            document.getElementById('current-time').textContent = timeString;
        };
        updateClock();
        setInterval(updateClock, 1000);
    }

    async loadAllData() {
        console.log('📡 Loading real data from APIs...');

        await Promise.allSettled([
            this.loadBitcoinPrice(),
            this.loadIndicators(),
            this.loadPriceHistory(),
            this.loadMarketDepth(),
            this.loadFundingRate(),
            this.loadNews(),
            this.loadTwitterFeed(),
            this.loadVolumeProfile()
        ]);

        console.log('✅ Real data loaded successfully');
    }

    async loadBitcoinPrice() {
        try {
            console.log('Fetching Bitcoin price from API...');
            const response = await fetch(`${this.apiBase}/data/current`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            const data = result.success ? result.data : result;

            console.log('✅ Bitcoin price data received:', data);
            this.currentPrice = data.price || 0;
            this.updatePriceDisplay(data);
        } catch (error) {
            console.error('❌ Error loading Bitcoin price:', error);
            this.showError('Failed to load Bitcoin price data');
        }
    }

    updatePriceDisplay(data) {
        const price = data.price || 0;
        const change = data.change_24h || 0;
        const high = data.high_24h || 0;
        const low = data.low_24h || 0;
        const volume = data.volume || data.volume_24h || 0;
        const marketCap = price * 19700000; // Approx circulating supply

        // Update DOM elements
        document.getElementById('btc-price').textContent = `$${price.toLocaleString()}`;
        document.getElementById('change-value').textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
        document.getElementById('change-value').className = change >= 0 ? 'text-green' : 'text-red';
        document.getElementById('change-absolute').textContent = `$${(price * change / 100).toFixed(2)}`;
        document.getElementById('high-24h').textContent = high > 0 ? `$${high.toLocaleString()}` : 'Loading...';
        document.getElementById('low-24h').textContent = low > 0 ? `$${low.toLocaleString()}` : 'Loading...';
        document.getElementById('volume-24h').textContent = volume > 0 ? `${volume.toLocaleString()} BTC` : 'Loading...';
        document.getElementById('market-cap').textContent = `$${(marketCap / 1e9).toFixed(2)}B`;

        // Update Hyperliquid-specific data if available
        if (data.source === 'hyperliquid') {
            // Funding rate
            if (data.funding_rate !== undefined) {
                const fundingEl = document.getElementById('funding-rate');
                if (fundingEl) {
                    const fundingRate = data.funding_rate;
                    fundingEl.textContent = `${fundingRate >= 0 ? '+' : ''}${fundingRate.toFixed(4)}%`;
                    fundingEl.className = `funding-value ${fundingRate >= 0 ? 'funding-positive' : 'funding-negative'}`;
                }
            }

            // Open interest
            if (data.open_interest !== undefined) {
                const oiEl = document.getElementById('open-interest');
                if (oiEl) {
                    oiEl.textContent = `${data.open_interest.toLocaleString()} BTC`;
                }
            }
        }
    }

    async loadIndicators() {
        try {
            console.log('Fetching technical indicators...');
            const response = await fetch(`${this.apiBase}/strategies/list`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            let strategies = [];

            if (result.success && result.data && result.data.strategies) {
                strategies = result.data.strategies;
            } else if (result.strategies) {
                strategies = result.strategies;
            }

            console.log('✅ Indicators data received:', strategies);
            this.updateIndicators(strategies);
        } catch (error) {
            console.error('❌ Error loading indicators:', error);
            this.setIndicatorLoading();
        }
    }

    updateIndicators(strategies) {
        const indicatorMap = {
            'rsi': 'rsi',
            'macd': 'macd',
            'bollinger_bands': 'bb',
            'moving_average': 'ma'
        };

        strategies.forEach(strategy => {
            const key = indicatorMap[strategy.type];
            if (!key) return;

            const signal = strategy.last_signal?.type || 'hold';
            const signalClass = signal === 'buy' ? 'signal-buy' : signal === 'sell' ? 'signal-sell' : 'signal-neutral';

            // Get real value from strategy data
            let value = '--';
            if (strategy.last_signal?.value !== undefined) {
                value = strategy.last_signal.value.toFixed(2);
            } else if (strategy.return !== undefined) {
                value = strategy.return.toFixed(2) + '%';
            }

            const valueEl = document.getElementById(`${key}-value`);
            const signalEl = document.getElementById(`${key}-signal`);

            if (valueEl) valueEl.textContent = value;
            if (signalEl) {
                signalEl.textContent = signal.toUpperCase();
                signalEl.className = `indicator-signal ${signalClass}`;
            }
        });
    }

    setIndicatorLoading() {
        ['rsi', 'macd', 'bb', 'ma'].forEach(key => {
            const valueEl = document.getElementById(`${key}-value`);
            const signalEl = document.getElementById(`${key}-signal`);
            if (valueEl) valueEl.textContent = '--';
            if (signalEl) {
                signalEl.textContent = 'NO DATA';
                signalEl.className = 'indicator-signal signal-neutral';
            }
        });
    }

    async loadPriceHistory() {
        try {
            console.log('Fetching price history...');
            const response = await fetch(`${this.apiBase}/data/history/24`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            const data = result.success ? result.data : result;

            if (data.history && this.charts.price) {
                console.log('✅ Price history received, updating chart');
                this.updatePriceChart(data.history);
            }
        } catch (error) {
            console.error('❌ Error loading price history:', error);
        }
    }

    async loadMarketDepth() {
        try {
            // Try Binance API first (may be geo-restricted)
            console.log('📊 Fetching real market depth...');
            let response = await fetch('https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=50');

            // If Binance fails (geo-restriction), try through our backend or alternative
            if (!response.ok || response.status === 451) {
                console.log('⚠️ Binance API unavailable (geo-restriction), trying alternatives...');

                // Try CoinGecko as fallback (no order book depth available on free tier)
                // Show informative message instead
                this.showDepthUnavailable();
                return;
            }

            const data = await response.json();

            // Check for Binance error response
            if (data.code === 0 && data.msg) {
                console.log('⚠️ Binance API restricted:', data.msg);
                this.showDepthUnavailable();
                return;
            }

            console.log('✅ Real order book data received');
            this.updateDepthChart(data);
        } catch (error) {
            console.error('❌ Error loading market depth:', error);
            this.showDepthUnavailable();
        }
    }

    updateDepthChart(data) {
        if (!data.bids || !data.asks) return;

        const bids = data.bids.slice(0, 30);
        const asks = data.asks.slice(0, 30);

        const bidPrices = [];
        const bidVolumes = [];
        const askPrices = [];
        const askVolumes = [];

        let cumBid = 0;
        bids.reverse().forEach(([price, volume]) => {
            cumBid += parseFloat(volume);
            bidPrices.push(parseFloat(price));
            bidVolumes.push(cumBid);
        });

        let cumAsk = 0;
        asks.forEach(([price, volume]) => {
            cumAsk += parseFloat(volume);
            askPrices.push(parseFloat(price));
            askVolumes.push(cumAsk);
        });

        const traces = [
            {
                x: bidPrices,
                y: bidVolumes,
                fill: 'tozeroy',
                type: 'scatter',
                mode: 'lines',
                name: 'Bids',
                line: { color: '#00ff88', width: 2 }
            },
            {
                x: askPrices,
                y: askVolumes,
                fill: 'tozeroy',
                type: 'scatter',
                mode: 'lines',
                name: 'Asks',
                line: { color: '#ff3366', width: 2 }
            }
        ];

        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            xaxis: {
                color: '#8b92b0',
                gridcolor: 'rgba(139, 146, 176, 0.1)',
                title: 'Price (USDT)'
            },
            yaxis: {
                color: '#8b92b0',
                gridcolor: 'rgba(139, 146, 176, 0.1)',
                title: 'Cumulative Volume (BTC)'
            },
            showlegend: true,
            legend: {
                font: { color: '#8b92b0' },
                bgcolor: 'transparent'
            },
            margin: { t: 20, r: 20, b: 40, l: 60 }
        };

        Plotly.newPlot('depth-chart', traces, layout, {displayModeBar: false});
    }

    showPlaceholderDepth() {
        document.getElementById('depth-chart').innerHTML =
            '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary);">Unable to load order book data</div>';
    }

    showDepthUnavailable() {
        document.getElementById('depth-chart').innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; flex-direction: column; color: var(--text-secondary);">
                <div style="font-size: 1.2rem; margin-bottom: 1rem;">📊 Order Book Depth</div>
                <div style="font-size: 0.875rem;">Real-time order book unavailable</div>
                <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.7;">Binance API geo-restricted in your region</div>
                <div style="font-size: 0.75rem; opacity: 0.7;">Free alternatives don't provide order book depth data</div>
            </div>
        `;
    }

    async loadFundingRate() {
        try {
            // Try Binance Futures API for funding rate
            console.log('📊 Fetching real funding rate...');
            const response = await fetch('https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT');

            if (!response.ok || response.status === 451) {
                console.log('⚠️ Binance Futures API unavailable (geo-restriction)');
                this.setFundingUnavailable();
                return;
            }

            const data = await response.json();

            // Check for Binance error response
            if (data.code === 0 && data.msg) {
                console.log('⚠️ Binance Futures API restricted:', data.msg);
                this.setFundingUnavailable();
                return;
            }

            console.log('✅ Real funding rate received:', data);
            this.updateFundingRate(data);
        } catch (error) {
            console.error('❌ Error loading funding rate:', error);
            this.setFundingUnavailable();
        }
    }

    updateFundingRate(data) {
        const fundingRate = parseFloat(data.lastFundingRate) * 100;
        const fundingEl = document.getElementById('funding-rate');

        if (fundingEl) {
            fundingEl.textContent = `${fundingRate >= 0 ? '+' : ''}${fundingRate.toFixed(4)}%`;
            fundingEl.className = `funding-value ${fundingRate >= 0 ? 'funding-positive' : 'funding-negative'}`;
        }

        // Update countdown
        const nextFundingTime = parseInt(data.nextFundingTime);
        const updateCountdown = () => {
            const now = Date.now();
            const diff = nextFundingTime - now;

            if (diff > 0) {
                const hours = Math.floor(diff / 3600000);
                const minutes = Math.floor((diff % 3600000) / 60000);
                const seconds = Math.floor((diff % 60000) / 1000);
                const countdownEl = document.getElementById('funding-countdown');
                if (countdownEl) {
                    countdownEl.textContent = `${hours}h ${minutes}m ${seconds}s`;
                }
            }
        };

        updateCountdown();
        setInterval(updateCountdown, 1000);
    }

    setFundingPlaceholder() {
        const fundingEl = document.getElementById('funding-rate');
        if (fundingEl) {
            fundingEl.textContent = 'No Data';
            fundingEl.className = 'funding-value';
        }
    }

    setFundingUnavailable() {
        const fundingEl = document.getElementById('funding-rate');
        if (fundingEl) {
            fundingEl.textContent = 'Unavailable';
            fundingEl.className = 'funding-value';
            fundingEl.style.fontSize = '1.2rem';
        }
        const countdownEl = document.getElementById('funding-countdown');
        if (countdownEl) {
            countdownEl.textContent = 'API geo-restricted';
        }
    }

    async loadLiquidations() {
        // Note: Real liquidation data requires paid API access from services like:
        // - Coinglass API
        // - Bybit API
        // - FTX API (if available)
        // For now, we'll show a message that this requires premium data
        console.log('⚠️ Liquidation data requires premium API access');
        this.showLiquidationMessage();
    }

    showLiquidationMessage() {
        const heatmapEl = document.getElementById('liquidation-heatmap');
        if (heatmapEl) {
            heatmapEl.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; flex-direction: column; color: var(--text-secondary);">
                    <div style="font-size: 1.2rem; margin-bottom: 1rem;">📊 Liquidation Heatmap</div>
                    <div style="font-size: 0.875rem;">Real liquidation data requires premium API access</div>
                    <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.7;">Contact Coinglass, Bybit, or similar providers</div>
                </div>
            `;
        }

        const tbody = document.querySelector('#liquidations-table tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--text-secondary); padding: 2rem;">Liquidation feed requires premium API</td></tr>';
        }
    }

    initializeCharts() {
        this.initializePriceChart();
        this.initializeFundingChart();
        this.initializeOpenInterestChart();
    }

    initializePriceChart() {
        const ctx = document.getElementById('price-chart-canvas');
        if (!ctx) return;

        this.charts.price = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'BTC Price',
                    data: [],
                    borderColor: '#0099ff',
                    backgroundColor: 'rgba(0, 153, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'hour'
                        },
                        grid: {
                            color: 'rgba(139, 146, 176, 0.1)'
                        },
                        ticks: {
                            color: '#8b92b0'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(139, 146, 176, 0.1)'
                        },
                        ticks: {
                            color: '#8b92b0',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    updatePriceChart(history) {
        if (!this.charts.price || !history || history.length === 0) return;

        const data = history.map(item => ({
            x: new Date(item.timestamp * 1000),
            y: item.price
        }));

        this.charts.price.data.datasets[0].data = data;
        this.charts.price.update();
    }

    initializeFundingChart() {
        const ctx = document.getElementById('funding-chart');
        if (!ctx) return;

        this.charts.funding = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['No Data'],
                datasets: [{
                    data: [0],
                    backgroundColor: ['#8b92b0']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#8b92b0'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(139, 146, 176, 0.1)'
                        },
                        ticks: {
                            color: '#8b92b0',
                            callback: function(value) {
                                return value.toFixed(3) + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    initializeOpenInterestChart() {
        const ctx = document.getElementById('oi-chart');
        if (!ctx) return;

        this.charts.openInterest = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['No Data'],
                datasets: [{
                    label: 'Open Interest',
                    data: [0],
                    borderColor: '#0099ff',
                    backgroundColor: 'rgba(0, 153, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#8b92b0'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(139, 146, 176, 0.1)'
                        },
                        ticks: {
                            color: '#8b92b0',
                            callback: function(value) {
                                return value.toLocaleString() + ' BTC';
                            }
                        }
                    }
                }
            }
        });
    }

    async loadNews() {
        try {
            console.log('📰 Fetching crypto news...');

            // Using CoinGecko's trending search API (free, no key required)
            const response = await fetch('https://api.coingecko.com/api/v3/search/trending');

            if (!response.ok) {
                throw new Error('News API unavailable');
            }

            const data = await response.json();
            console.log('✅ Trending data received');

            // Transform trending data into news-like format
            const trendingCoins = data.coins || [];
            const newsItems = trendingCoins.map((coin, index) => ({
                title: `${coin.item.name} (${coin.item.symbol}) - Rank #${coin.item.market_cap_rank || 'N/A'}`,
                subtitle: `24h Price: ${coin.item.data?.price || 'N/A'} | Market Cap: $${(coin.item.data?.market_cap || 0).toLocaleString()}`,
                url: `https://www.coingecko.com/en/coins/${coin.item.id}`,
                source: 'CoinGecko Trending',
                score: coin.item.score || index,
                timestamp: new Date()
            }));

            this.displayTrendingNews(newsItems);
        } catch (error) {
            console.error('❌ Error loading news:', error);
            this.showNewsError();
        }
    }

    displayTrendingNews(items) {
        const newsContainer = document.getElementById('news-feed');
        if (!newsContainer) return;

        if (items.length === 0) {
            newsContainer.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">No trending data available</div>';
            return;
        }

        newsContainer.innerHTML = items.map((item, index) => {
            return `
                <div class="news-item" onclick="window.open('${item.url}', '_blank')">
                    <div class="news-title">#${index + 1} ${this.escapeHtml(item.title)}</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">
                        ${this.escapeHtml(item.subtitle)}
                    </div>
                    <div class="news-meta" style="margin-top: 0.5rem;">
                        <span class="news-source">${this.escapeHtml(item.source)}</span>
                        <span class="text-green">🔥 Trending</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    showNewsError() {
        const newsContainer = document.getElementById('news-feed');
        if (newsContainer) {
            newsContainer.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">News feed temporarily unavailable</div>';
        }
    }

    async loadTwitterFeed() {
        try {
            console.log('𝕏 Loading crypto Twitter feed...');

            // Using Nitter RSS-to-JSON for free Twitter data
            // Alternative: We'll show curated crypto Twitter accounts
            const accounts = [
                { username: 'Bitcoin', handle: '@Bitcoin', text: 'Bitcoin is a swarm of cyber hornets serving the goddess of wisdom, feeding on the fire of truth' },
                { username: 'Vitalik Buterin', handle: '@VitalikButerin', text: 'Ethereum and crypto updates' },
                { username: 'CZ', handle: '@cz_binance', text: 'Crypto market insights' },
                { username: 'Willy Woo', handle: '@woonomic', text: 'On-chain analytics and Bitcoin insights' }
            ];

            // Try to fetch real Twitter/X data via RSS bridge or Nitter
            // For now, show placeholder with links to follow these accounts
            this.displayTwitterPlaceholder(accounts);

        } catch (error) {
            console.error('❌ Error loading Twitter feed:', error);
            this.showTwitterError();
        }
    }

    displayTwitterPlaceholder(accounts) {
        const twitterContainer = document.getElementById('twitter-feed');
        if (!twitterContainer) return;

        twitterContainer.innerHTML = `
            <div style="padding: 1rem;">
                <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 1rem;">
                    Follow these accounts for Bitcoin insights:
                </div>
                ${accounts.map(account => `
                    <div class="tweet-item" onclick="window.open('https://twitter.com/${account.handle.replace('@', '')}', '_blank')">
                        <div class="tweet-author">
                            <span class="tweet-username">${account.username}</span>
                            <span class="tweet-handle">${account.handle}</span>
                        </div>
                        <div class="tweet-text">${account.text}</div>
                        <div class="tweet-meta">Click to follow →</div>
                    </div>
                `).join('')}
                <div style="margin-top: 1rem; padding: 1rem; background: rgba(0, 153, 255, 0.1); border-radius: 8px; font-size: 0.875rem;">
                    💡 <strong>Note:</strong> Real-time Twitter feed requires authentication. This shows recommended accounts to follow.
                </div>
            </div>
        `;
    }

    showTwitterError() {
        const twitterContainer = document.getElementById('twitter-feed');
        if (twitterContainer) {
            twitterContainer.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">Twitter feed unavailable</div>';
        }
    }

    async loadVolumeProfile() {
        try {
            console.log('📊 Creating volume profile...');

            // Get price history to build volume profile
            const response = await fetch(`${this.apiBase}/data/history/168`); // 7 days

            if (!response.ok) {
                throw new Error('Failed to fetch history for volume profile');
            }

            const result = await response.json();
            const history = result.success ? result.data.history : result.history;

            if (history && history.length > 0) {
                this.createVolumeProfile(history);
            }
        } catch (error) {
            console.error('❌ Error loading volume profile:', error);
            this.showVolumeProfileError();
        }
    }

    createVolumeProfile(history) {
        // Create price buckets
        const prices = history.map(h => h.price);
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);

        const bucketCount = 30;
        const bucketSize = (maxPrice - minPrice) / bucketCount;

        // Aggregate volume by price level
        const buckets = new Array(bucketCount).fill(0).map((_, i) => ({
            price: minPrice + (i * bucketSize),
            volume: 0
        }));

        history.forEach(candle => {
            const bucketIndex = Math.min(
                Math.floor((candle.price - minPrice) / bucketSize),
                bucketCount - 1
            );
            buckets[bucketIndex].volume += candle.volume || 0;
        });

        // Create horizontal bar chart with Plotly
        const trace = {
            y: buckets.map(b => `$${b.price.toFixed(0)}`),
            x: buckets.map(b => b.volume),
            type: 'bar',
            orientation: 'h',
            marker: {
                color: buckets.map(b => {
                    const intensity = b.volume / Math.max(...buckets.map(b2 => b2.volume));
                    return `rgba(0, 153, 255, ${0.3 + intensity * 0.7})`;
                })
            }
        };

        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            xaxis: {
                color: '#8b92b0',
                gridcolor: 'rgba(139, 146, 176, 0.1)',
                title: 'Volume (BTC)'
            },
            yaxis: {
                color: '#8b92b0',
                gridcolor: 'rgba(139, 146, 176, 0.1)',
                title: 'Price Level'
            },
            margin: { t: 20, r: 20, b: 40, l: 80 },
            showlegend: false
        };

        Plotly.newPlot('volume-profile', [trace], layout, {displayModeBar: false});
    }

    showVolumeProfileError() {
        const vpContainer = document.getElementById('volume-profile');
        if (vpContainer) {
            vpContainer.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary);">Volume profile unavailable</div>';
        }
    }

    getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);

        let interval = seconds / 31536000;
        if (interval > 1) return Math.floor(interval) + 'y ago';

        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + 'mo ago';

        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + 'd ago';

        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + 'h ago';

        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + 'm ago';

        return Math.floor(seconds) + 's ago';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        console.error('Dashboard Error:', message);
    }

    startAutoUpdate() {
        console.log('🔄 Starting auto-update (30s interval)');

        // Update price and indicators every 30 seconds
        this.intervals.push(setInterval(() => {
            console.log('🔄 Auto-updating data...');
            this.loadBitcoinPrice();
            this.loadIndicators();
        }, this.updateInterval));

        // Update market depth every 60 seconds
        this.intervals.push(setInterval(() => {
            this.loadMarketDepth();
        }, 60000));

        // Update news every 5 minutes
        this.intervals.push(setInterval(() => {
            this.loadNews();
        }, 300000));
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌐 DOM loaded, initializing dashboard...');
    window.dashboard = new AnalyticsDashboard();
});
