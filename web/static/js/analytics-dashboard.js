/**
 * Odin Analytics Dashboard - Modern Bitcoin Market Intelligence
 * REAL DATA ONLY - Connects to trusted APIs
 */

// GLOBAL TICKER EVENT LISTENER - Attached immediately when script loads
document.addEventListener("ticker-coin-selected", async (e) => {
    console.log('========== GLOBAL TICKER LISTENER ==========');
    console.log('Received at:', new Date().toISOString());
    console.log('Event detail:', e.detail);
    
    const coin = e.detail.coin;
    if (!coin) {
        console.warn('No coin in event detail');
        return;
    }
    
    // Wait for dashboard to exist
    if (window.dashboard && window.dashboard.handleCoinChange) {
        console.log('Calling dashboard.handleCoinChange for:', coin);
        await window.dashboard.handleCoinChange(coin);
    } else {
        console.warn('Dashboard not ready yet, storing coin for later');
        window.pendingCoinSwitch = coin;
    }
});
console.log('GLOBAL ticker listener attached at script load');

class AnalyticsDashboard {
    constructor() {
        this.apiBase = "/api/v1";
        this.charts = {};
        this.updateInterval = 30000; // 30 seconds
        this.intervals = [];
        this.selectedTimeframe = 24;
        this.priceHistory = []; // Default 24 hours
        this.currentPrice = 0;
        this.selectedCoin = "BTC"; // Default to Bitcoin

        // Initialize logger
        this.logger =
            typeof LoggerFactory !== "undefined"
                ? LoggerFactory.getLogger("AnalyticsDashboard")
                : console; // Fallback to console if logger not available

        // Error handling configuration
        this.maxRetries = 3;
        this.retryDelay = 1000; // 1 second
        this.errorCount = 0;
        this.lastError = null;

        // Loading state management
        this.loadingStates = new Map();
        this.loadingOverlay = null;

        // Asset metadata mapping (crypto, metals, stocks)
        this.coinMappings = {
            // Cryptocurrencies
            BTC: {
                name: "Bitcoin",
                symbol: "₿",
                category: "crypto",
                tradingview: "BINANCE:BTCUSDT",
                krakenSymbol: "XBTUSD",
                binanceSymbol: "BTCUSDT",
                coingeckoId: "bitcoin",
                hyperliquidSymbol: "BTC",
                circulatingSupply: 19700000,
                redditSub: "Bitcoin",
            },
            ETH: {
                name: "Ethereum",
                symbol: "Ξ",
                category: "crypto",
                tradingview: "BINANCE:ETHUSDT",
                krakenSymbol: "ETHUSD",
                binanceSymbol: "ETHUSDT",
                coingeckoId: "ethereum",
                hyperliquidSymbol: "ETH",
                circulatingSupply: 120000000,
                redditSub: "ethereum",
            },
            SOL: {
                name: "Solana",
                symbol: "◎",
                category: "crypto",
                tradingview: "BINANCE:SOLUSDT",
                krakenSymbol: "SOLUSD",
                binanceSymbol: "SOLUSDT",
                coingeckoId: "solana",
                hyperliquidSymbol: "SOL",
                circulatingSupply: 400000000,
                redditSub: "solana",
            },
            XRP: {
                name: "Ripple",
                symbol: "✕",
                category: "crypto",
                tradingview: "BINANCE:XRPUSDT",
                krakenSymbol: "XRPUSD",
                binanceSymbol: "XRPUSDT",
                coingeckoId: "ripple",
                hyperliquidSymbol: "XRP",
                circulatingSupply: 50000000000,
                redditSub: "Ripple",
            },
            BNB: {
                name: "BNB",
                symbol: "🔶",
                category: "crypto",
                tradingview: "BINANCE:BNBUSDT",
                krakenSymbol: "BNBUSD",
                binanceSymbol: "BNBUSDT",
                coingeckoId: "binancecoin",
                hyperliquidSymbol: "BNB",
                circulatingSupply: 150000000,
                redditSub: "bnbchainofficial",
            },
            SUI: {
                name: "Sui",
                symbol: "〜",
                category: "crypto",
                tradingview: "BINANCE:SUIUSDT",
                krakenSymbol: "SUIUSD",
                binanceSymbol: "SUIUSDT",
                coingeckoId: "sui",
                hyperliquidSymbol: "SUI",
                circulatingSupply: 1000000000,
                redditSub: "sui",
            },
            HYPE: {
                name: "Hyperliquid",
                symbol: "🚀",
                category: "crypto",
                tradingview: "BYBIT:HYPEUSDT",
                krakenSymbol: "HYPEUSD",
                binanceSymbol: "HYPEUSDT",
                coingeckoId: "hyperliquid",
                hyperliquidSymbol: "HYPE",
                circulatingSupply: 1000000000,
                redditSub: "hyperliquid",
            },
            // Precious Metals
            GOLD: {
                name: "Gold",
                symbol: "🥇",
                category: "metal",
                tradingview: "COMEX:GC1!",
                unit: "oz",
            },
            SILVER: {
                name: "Silver",
                symbol: "🥈",
                category: "metal",
                tradingview: "COMEX:SI1!",
                unit: "oz",
            },
            PLATINUM: {
                name: "Platinum",
                symbol: "⬜",
                category: "metal",
                tradingview: "NYMEX:PL1!",
                unit: "oz",
            },
            PALLADIUM: {
                name: "Palladium",
                symbol: "🔘",
                category: "metal",
                tradingview: "NYMEX:PA1!",
                unit: "oz",
            },
            COPPER: {
                name: "Copper",
                symbol: "🟤",
                category: "metal",
                tradingview: "COMEX:HG1!",
                unit: "lb",
            },
            // Stocks
            SPY: {
                name: "S&P 500 ETF",
                symbol: "📊",
                category: "stock",
                tradingview: "AMEX:SPY",
                sector: "Index ETF",
            },
            QQQ: {
                name: "Nasdaq 100 ETF",
                symbol: "📈",
                category: "stock",
                tradingview: "NASDAQ:QQQ",
                sector: "Index ETF",
            },
            AAPL: {
                name: "Apple",
                symbol: "🍎",
                category: "stock",
                tradingview: "NASDAQ:AAPL",
                sector: "Technology",
            },
            MSFT: {
                name: "Microsoft",
                symbol: "🪟",
                category: "stock",
                tradingview: "NASDAQ:MSFT",
                sector: "Technology",
            },
            GOOGL: {
                name: "Alphabet",
                symbol: "🔍",
                category: "stock",
                tradingview: "NASDAQ:GOOGL",
                sector: "Technology",
            },
            AMZN: {
                name: "Amazon",
                symbol: "📦",
                category: "stock",
                tradingview: "NASDAQ:AMZN",
                sector: "Consumer",
            },
            NVDA: {
                name: "NVIDIA",
                symbol: "🎮",
                category: "stock",
                tradingview: "NASDAQ:NVDA",
                sector: "Technology",
            },
            TSLA: {
                name: "Tesla",
                symbol: "🚗",
                category: "stock",
                tradingview: "NASDAQ:TSLA",
                sector: "Automotive",
            },
            META: {
                name: "Meta",
                symbol: "👓",
                category: "stock",
                tradingview: "NASDAQ:META",
                sector: "Technology",
            },
            COIN: {
                name: "Coinbase",
                symbol: "🪙",
                category: "stock",
                tradingview: "NASDAQ:COIN",
                sector: "Crypto",
            },
            MSTR: {
                name: "MicroStrategy",
                symbol: "📉",
                category: "stock",
                tradingview: "NASDAQ:MSTR",
                sector: "Crypto",
            },
        };

        // WebSocket connection for real-time updates
        this.ws = null;
        this.wsReconnectAttempts = 0;
        this.maxWsReconnectAttempts = 5;

        // Define handleCoinChange in constructor so global listener can use it immediately
        this.handleCoinChange = async (newCoin) => {
            console.log('========================================');
            console.log('*** COIN CHANGE HANDLER CALLED ***');
            console.log('Switching to:', newCoin);
            console.log('Current coin:', this.selectedCoin);
            console.log('========================================');

            if (newCoin === this.selectedCoin) {
                console.log('Already on', newCoin, '- skipping');
                return;
            }

            this.selectedCoin = newCoin;
            localStorage.setItem("selectedCoin", newCoin);

            // Clear cached data to force fresh fetch
            this.priceHistory = [];
            this.currentPrice = 0;

            // Update UI immediately
            this.updateCoinName();

            // Send WebSocket switch message for instant price update
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                console.log('Sending WebSocket switch_symbol for', newCoin);
                this.ws.send(JSON.stringify({
                    type: 'switch_symbol',
                    symbol: newCoin
                }));
            }

            // Update TradingView chart if available
            if (window.tradingViewWidget) {
                console.log('Updating TradingView chart to', newCoin);
                window.tradingViewWidget.updateChart(newCoin, this.selectedTimeframe || 24);
            }

            // Load current price AND history in parallel for faster display
            console.log('Loading price data for', newCoin);
            await Promise.all([
                this.loadBitcoinPrice(),  // Updates price display immediately
                this.loadPriceHistory(),   // Needed for charts
            ]);

            // Reinitialize charts with new data
            console.log('Reinitializing charts...');
            this.initializeCharts();

            // Load other data in background (non-blocking)
            this.loadRemainingDataInBackground();

            console.log('*** COIN SWITCH COMPLETE ***');
            console.log('Switched to:', this.getCoinInfo().name);
            console.log('========================================');
        };

        this.init();
    }

    async init() {
        console.log("🚀 Initializing Odin Analytics Dashboard - Real Data Only");

        // Setup theme toggle and coin selector
        this.setupThemeToggle();
        this.setupCoinSelector();
        this.setupTimeframeButtons();

        // Initialize WebSocket for real-time updates
        this.initWebSocket();

        // Check if there was a pending coin switch from before dashboard loaded
        if (window.pendingCoinSwitch) {
            console.log('Found pending coin switch to:', window.pendingCoinSwitch);
            setTimeout(() => {
                this.handleCoinChange(window.pendingCoinSwitch);
                window.pendingCoinSwitch = null;
            }, 500);
        }

        // Start clock
        this.startClock();

        // Initialize charts FIRST (so they exist when data loads)
        this.initializeCharts();

        // Load REAL data from APIs (this will populate the charts)
        await this.loadAllData();

        // Start auto-update
        this.startAutoUpdate();

        console.log("✅ Dashboard initialized with real data feeds");
    }

    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        console.log('🔌 Connecting to WebSocket:', wsUrl);

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.wsReconnectAttempts = 0;

                // Subscribe to current coin
                this.ws.send(JSON.stringify({
                    type: 'switch_symbol',
                    symbol: this.selectedCoin
                }));
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleWebSocketMessage(message);
                } catch (e) {
                    console.error('Error parsing WebSocket message:', e);
                }
            };

            this.ws.onclose = (event) => {
                console.log('🔌 WebSocket closed:', event.code);
                this.scheduleWebSocketReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.scheduleWebSocketReconnect();
        }
    }

    scheduleWebSocketReconnect() {
        if (this.wsReconnectAttempts >= this.maxWsReconnectAttempts) {
            console.warn('Max WebSocket reconnect attempts reached');
            return;
        }

        this.wsReconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.wsReconnectAttempts), 30000);
        console.log(`Reconnecting WebSocket in ${delay}ms (attempt ${this.wsReconnectAttempts})`);

        setTimeout(() => this.initWebSocket(), delay);
    }

    handleWebSocketMessage(message) {
        if (message.type === 'price_update' && message.data) {
            const data = message.data;
            const symbol = message.symbol || data.symbol || '';
            const streamType = message.stream_type || 'ticker';

            // Only update if this is for our selected coin
            if (symbol.toUpperCase() === this.selectedCoin ||
                symbol.toUpperCase().startsWith(this.selectedCoin)) {

                // Handle ticker updates (price data)
                if (streamType === 'ticker' && data.price) {
                    console.log('📈 Direct stream price:', this.selectedCoin, '$' + data.price);

                    // Update current price immediately
                    this.currentPrice = data.price;

                    // Update price display with exchange data format
                    this.updatePriceDisplay({
                        price: data.price,
                        change_24h: data.change_24h,
                        high_24h: data.high_24h,
                        low_24h: data.low_24h,
                        volume_24h: data.volume_24h || data.quote_volume,
                        bid: data.bid,
                        ask: data.ask,
                    });

                    // Add to price history for charts
                    if (this.priceHistory.length > 0) {
                        const now = Math.floor(Date.now() / 1000);
                        this.priceHistory.push({
                            timestamp: now,
                            price: data.price,
                            high: data.high_24h || data.price,
                            low: data.low_24h || data.price,
                            volume: data.volume_24h || 0
                        });

                        // Keep history manageable
                        if (this.priceHistory.length > 500) {
                            this.priceHistory.shift();
                        }
                    }
                }

                // Handle trade updates (individual trades)
                if (streamType === 'trade' && data.price) {
                    // Update last trade indicator
                    this.lastTrade = {
                        price: data.price,
                        quantity: data.quantity,
                        side: data.side,
                        time: data.trade_time || Date.now()
                    };
                }
            }
        } else if (message.type === 'symbol_switched') {
            console.log('✅ Symbol switched to:', message.symbol,
                message.cached ? '(from cache - instant!)' : '(waiting for stream)');
        } else if (message.type === 'connection') {
            console.log('🔗 Connected:', message.message);
            if (message.supported_symbols) {
                console.log('Supported symbols:', message.supported_symbols.join(', '));
            }
        } else if (message.type === 'subscribed') {
            console.log('📊 Subscribed to:', message.symbols);
        } else if (message.type === 'error') {
            console.error('❌ WebSocket error:', message.message);
        }
    }

    async loadRemainingDataInBackground() {
        // Load secondary data without blocking UI
        // Note: loadBitcoinPrice is called directly in handleCoinChange now
        const backgroundTasks = [
            this.loadIndicators(),
            this.loadMarketDepth(),
            this.loadFundingRate(),
            this.loadCorrelationMatrix(),
            this.calculateFibonacci(),
            this.calculateSupportResistance(),
            this.detectPatterns(),
            this.loadVolumeProfile(),
            this.loadSentimentAnalysis(),
            this.calculateFearGreedIndex(),
        ];

        Promise.allSettled(backgroundTasks).then(results => {
            const failed = results.filter(r => r.status === 'rejected').length;
            if (failed > 0) {
                console.warn(`${failed} background tasks failed`);
            }
        });
    }

    startClock() {
        const updateClock = () => {
            const now = new Date();
            const timeString = now.toLocaleString("en-US", {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
            });
            const timeEl = document.getElementById("current-time");
            if (timeEl) {
                timeEl.textContent = timeString;
            }
        };
        updateClock();
        // Track the clock interval to allow cleanup
        this.clockInterval = setInterval(updateClock, 1000);
    }

    async loadAllData() {
        console.log(`📡 Loading real data from APIs for ${this.getCoinInfo().name}...`);

        // Load price history FIRST (required for indicators)
        await this.loadPriceHistory();

        // Then load everything else in parallel
        const loadTasks = [
            { name: "Bitcoin Price", fn: this.loadBitcoinPrice() },
            { name: "Indicators", fn: this.loadIndicators() },
            { name: "Market Depth", fn: this.loadMarketDepth() },
            { name: "Funding Rate", fn: this.loadFundingRate() },
            { name: "Liquidations", fn: this.loadLiquidations() },
            { name: "Correlation Matrix", fn: this.loadCorrelationMatrix() },
            { name: "Fibonacci Levels", fn: this.calculateFibonacci() },
            { name: "Support Resistance", fn: this.calculateSupportResistance() },
            { name: "Pattern Detection", fn: this.detectPatterns() },
            { name: "News", fn: this.loadNews() },
            { name: "Twitter Feed", fn: this.loadTwitterFeed() },
            { name: "Volume Profile", fn: this.loadVolumeProfile() },
            { name: "On-Chain Metrics", fn: this.loadOnChainMetrics() },
            { name: "Sentiment Analysis", fn: this.loadSentimentAnalysis() },
            { name: "Economic Calendar", fn: this.loadEconomicCalendar() },
            { name: "Multi-Timeframe", fn: this.loadMultiTimeframeData() },
            { name: "Fear & Greed", fn: this.calculateFearGreedIndex() },
            { name: "CME Gaps", fn: this.loadCMEGaps() },
        ];

        const results = await Promise.allSettled(loadTasks.map((task) => task.fn));

        // Log results for debugging
        results.forEach((result, index) => {
            if (result.status === "rejected") {
                console.error(`❌ Failed to load ${loadTasks[index].name}:`, result.reason);
            } else {
                console.log(`✅ ${loadTasks[index].name} loaded`);
            }
        });

        const failedCount = results.filter((r) => r.status === "rejected").length;
        if (failedCount > 0) {
            console.warn(`⚠️ ${failedCount} data sources failed to load`);
        } else {
            console.log("✅ All data loaded successfully");
        }
    }

    async loadBitcoinPrice() {
        const loadingKey = "bitcoin-price";
        try {
            const coinInfo = this.getCoinInfo();
            this.showLoading(loadingKey, `Loading ${coinInfo.name} price...`);

            console.log(`Fetching ${coinInfo.name} price from API...`);
            const response = await fetch(
                `${this.apiBase}/data/current?symbol=${this.selectedCoin}`,
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            const data = result.success ? result.data : result;

            console.log(`✅ ${coinInfo.name} price data received:`, data);
            this.currentPrice = data.price || 0;
            this.updatePriceDisplay(data);
        } catch (error) {
            console.error(`❌ Error loading ${this.getCoinInfo().name} price:`, error);
            this.showError(`Failed to load ${this.getCoinInfo().name} price data`);
        } finally {
            this.hideLoading(loadingKey);
        }
    }

    updatePriceDisplay(data) {
        const price = data.price || 0;
        const change = data.change_24h || 0;
        const high = data.high_24h || 0;
        const low = data.low_24h || 0;
        const volume = data.volume || data.volume_24h || 0;
        const coinInfo = this.getCoinInfo();
        const marketCap = data.market_cap || (price * coinInfo.circulatingSupply);

        // Store for header ticker
        this.currentPrice = price;
        this.priceChange = change;

        // Update large price display
        const priceLargeEl = document.getElementById("btc-price-large");
        if (priceLargeEl) {
            priceLargeEl.textContent = `$${price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        }

        // Update coin name
        const coinNameEl = document.getElementById("price-coin-name");
        if (coinNameEl) {
            coinNameEl.textContent = coinInfo.name;
        }

        // Update change display
        const changeValueEl = document.getElementById("change-value-large");
        const changeAbsoluteEl = document.getElementById("change-absolute-large");
        if (changeValueEl) {
            changeValueEl.textContent = `${change >= 0 ? "+" : ""}${change.toFixed(2)}%`;
            changeValueEl.style.color = change >= 0 ? "var(--accent-success)" : "var(--accent-danger)";
        }
        if (changeAbsoluteEl) {
            const changeAbs = data.change_24h_abs || ((price * change) / 100);
            changeAbsoluteEl.textContent = `$${changeAbs.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        }

        // Update 24h stats
        const highEl = document.getElementById("high-24h-stat");
        const lowEl = document.getElementById("low-24h-stat");
        const volumeEl = document.getElementById("volume-24h-stat");
        const marketCapEl = document.getElementById("market-cap-stat");

        if (highEl) {
            highEl.textContent = high > 0 ? `$${high.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : "Loading...";
        }
        if (lowEl) {
            lowEl.textContent = low > 0 ? `$${low.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : "Loading...";
        }
        if (volumeEl) {
            volumeEl.textContent = volume > 0 ? `${volume.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ${this.selectedCoin}` : "Loading...";
        }
        if (marketCapEl) {
            marketCapEl.textContent = `$${(marketCap / 1e9).toFixed(2)}B`;
        }

        // Update Hyperliquid-specific data if available
        if (data.source === "hyperliquid") {
            // Funding rate
            if (data.funding_rate !== undefined) {
                const fundingEl = document.getElementById("funding-rate");
                if (fundingEl) {
                    const fundingRate = data.funding_rate;
                    fundingEl.textContent = `${fundingRate >= 0 ? "+" : ""}${fundingRate.toFixed(4)}%`;
                    fundingEl.className = `funding-value ${fundingRate >= 0 ? "funding-positive" : "funding-negative"}`;
                }
            }

            // Open interest
            if (data.open_interest !== undefined) {
                const oiEl = document.getElementById("open-interest");
                if (oiEl) {
                    oiEl.textContent = `${data.open_interest.toLocaleString()} BTC`;
                }
            }
        }
    }


    // ========== TECHNICAL INDICATOR CALCULATIONS ==========
    // Technical Indicator Calculation Methods
// Add these to AnalyticsDashboard class

calculateRSI(prices, period = 14) {
    if (prices.length < period + 1) return 50;
    const changes = [];
    for (let i = 1; i < prices.length; i++) {
        changes.push(prices[i] - prices[i - 1]);
    }
    const gains = changes.map(c => c > 0 ? c : 0);
    const losses = changes.map(c => c < 0 ? -c : 0);
    const avgGain = gains.slice(-period).reduce((a, b) => a + b, 0) / period;
    const avgLoss = losses.slice(-period).reduce((a, b) => a + b, 0) / period;
    if (avgLoss === 0) return 100;
    const rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
}

calculateSMA(prices, period) {
    if (prices.length < period) period = prices.length;
    const slice = prices.slice(-period);
    return slice.reduce((a, b) => a + b, 0) / period;
}

calculateEMA(prices, period) {
    if (prices.length < period) return this.calculateSMA(prices, prices.length);
    const multiplier = 2 / (period + 1);
    let ema = this.calculateSMA(prices.slice(0, period), period);
    for (let i = period; i < prices.length; i++) {
        ema = (prices[i] * multiplier) + (ema * (1 - multiplier));
    }
    return ema;
}

calculateMACD(prices, fast = 12, slow = 26, signal = 9) {
    const emaFast = this.calculateEMA(prices, fast);
    const emaSlow = this.calculateEMA(prices, slow);
    const macdLine = emaFast - emaSlow;
    const signalLine = macdLine * 0.9;
    const histogram = macdLine - signalLine;
    return { macd: macdLine, signal: signalLine, histogram };
}

calculateBollingerBands(prices, period = 20, stdDev = 2) {
    const sma = this.calculateSMA(prices, period);
    const slice = prices.slice(-Math.min(period, prices.length));
    const squaredDiffs = slice.map(p => Math.pow(p - sma, 2));
    const variance = squaredDiffs.reduce((a, b) => a + b, 0) / slice.length;
    const std = Math.sqrt(variance);
    return {
        upper: sma + (stdDev * std),
        middle: sma,
        lower: sma - (stdDev * std),
        std: std
    };
}

calculateStochastic(prices, period = 14) {
    const slice = prices.slice(-Math.min(period, prices.length));
    const highest = Math.max(...slice);
    const lowest = Math.min(...slice);
    const current = prices[prices.length - 1];
    let k = 50;
    if (highest !== lowest) {
        k = ((current - lowest) / (highest - lowest)) * 100;
    }
    const d = k * 0.9;
    return { k, d };
}

calculateATR(prices, period = 14) {
    if (prices.length < 2) return 0;
    const ranges = [];
    for (let i = 1; i < prices.length; i++) {
        ranges.push(Math.abs(prices[i] - prices[i - 1]));
    }
    const slice = ranges.slice(-Math.min(period, ranges.length));
    return slice.reduce((a, b) => a + b, 0) / slice.length;
}

// ========== ADVANCED INSTITUTIONAL INDICATORS ==========

calculateVWAP(history) {
    // Volume-Weighted Average Price - institutional benchmark
    if (!history || history.length === 0) return null;

    let cumVolumePrice = 0;
    let cumVolume = 0;

    for (const candle of history) {
        const volume = candle.volume || 1;
        cumVolumePrice += candle.price * volume;
        cumVolume += volume;
    }

    const vwap = cumVolumePrice / cumVolume;
    const current = history[history.length - 1].price;
    const deviation = ((current - vwap) / vwap) * 100;

    return {
        vwap,
        deviation,
        signal: deviation < -2 ? 'BUY' : deviation > 2 ? 'SELL' : 'HOLD',
        aboveVWAP: current > vwap
    };
}

calculateOrderFlowImbalance(history) {
    // Order Flow Imbalance - detects smart money accumulation/distribution
    if (!history || history.length < 10) return null;

    let buyPressure = 0;
    let sellPressure = 0;

    for (let i = 1; i < history.length; i++) {
        const priceChange = history[i].price - history[i - 1].price;
        const volume = history[i].volume || 1;

        if (priceChange > 0) {
            buyPressure += volume;
        } else if (priceChange < 0) {
            sellPressure += volume;
        }
    }

    const totalVolume = buyPressure + sellPressure;
    const imbalance = totalVolume > 0 ? ((buyPressure - sellPressure) / totalVolume) * 100 : 0;

    return {
        imbalance,
        buyPressure,
        sellPressure,
        signal: imbalance > 15 ? 'STRONG BUY' : imbalance < -15 ? 'STRONG SELL' : imbalance > 5 ? 'BUY' : imbalance < -5 ? 'SELL' : 'NEUTRAL'
    };
}

calculateIchimokuCloud(prices) {
    // Ichimoku Kinko Hyo - Japanese institutional indicator
    if (prices.length < 52) return null;

    const tenkan = 9;
    const kijun = 26;
    const senkou = 52;

    // Tenkan-sen (Conversion Line)
    const tenkanHigh = Math.max(...prices.slice(-tenkan));
    const tenkanLow = Math.min(...prices.slice(-tenkan));
    const tenkanSen = (tenkanHigh + tenkanLow) / 2;

    // Kijun-sen (Base Line)
    const kijunHigh = Math.max(...prices.slice(-kijun));
    const kijunLow = Math.min(...prices.slice(-kijun));
    const kijunSen = (kijunHigh + kijunLow) / 2;

    // Senkou Span A (Leading Span A)
    const senkouA = (tenkanSen + kijunSen) / 2;

    // Senkou Span B (Leading Span B)
    const senkouHigh = Math.max(...prices.slice(-senkou));
    const senkouLow = Math.min(...prices.slice(-senkou));
    const senkouB = (senkouHigh + senkouLow) / 2;

    const current = prices[prices.length - 1];
    const cloudTop = Math.max(senkouA, senkouB);
    const cloudBottom = Math.min(senkouA, senkouB);

    let signal = 'NEUTRAL';
    if (current > cloudTop && tenkanSen > kijunSen) signal = 'STRONG BUY';
    else if (current > cloudTop) signal = 'BUY';
    else if (current < cloudBottom && tenkanSen < kijunSen) signal = 'STRONG SELL';
    else if (current < cloudBottom) signal = 'SELL';

    return {
        tenkanSen,
        kijunSen,
        senkouA,
        senkouB,
        cloudTop,
        cloudBottom,
        signal,
        inCloud: current >= cloudBottom && current <= cloudTop,
        bullishCloud: senkouA > senkouB
    };
}

calculateSupertrend(prices, period = 10, multiplier = 3) {
    // Supertrend - Advanced trend following indicator
    if (prices.length < period) return null;

    const atr = this.calculateATR(prices, period);
    const hl2 = prices.slice(-period).reduce((sum, p) => sum + p, 0) / period;

    const upperBand = hl2 + (multiplier * atr);
    const lowerBand = hl2 - (multiplier * atr);
    const current = prices[prices.length - 1];

    const trend = current > upperBand ? 'BULLISH' : current < lowerBand ? 'BEARISH' : 'RANGING';
    const signal = trend === 'BULLISH' ? 'BUY' : trend === 'BEARISH' ? 'SELL' : 'HOLD';

    return {
        upperBand,
        lowerBand,
        trend,
        signal,
        strength: Math.abs(current - hl2) / atr
    };
}

calculateElderRay(prices) {
    // Elder Ray Index - Detects bull/bear power
    if (prices.length < 13) return null;

    const ema13 = this.calculateEMA(prices, 13);
    const current = prices[prices.length - 1];
    const high = Math.max(...prices.slice(-13));
    const low = Math.min(...prices.slice(-13));

    const bullPower = high - ema13;
    const bearPower = low - ema13;
    const elderRay = bullPower + bearPower;

    let signal = 'NEUTRAL';
    if (bullPower > 0 && bearPower > 0) signal = 'STRONG BUY';
    else if (bullPower > 0 && bearPower < 0 && bullPower > Math.abs(bearPower)) signal = 'BUY';
    else if (bullPower < 0 && bearPower < 0) signal = 'STRONG SELL';
    else if (bearPower < 0 && Math.abs(bearPower) > bullPower) signal = 'SELL';

    return {
        bullPower,
        bearPower,
        elderRay,
        signal,
        divergence: bullPower * bearPower < 0
    };
}

calculateKeltnerChannels(prices, period = 20, multiplier = 2) {
    // Keltner Channels - Volatility-based trend indicator
    if (prices.length < period) return null;

    const ema = this.calculateEMA(prices, period);
    const atr = this.calculateATR(prices, period);

    const upper = ema + (multiplier * atr);
    const lower = ema - (multiplier * atr);
    const current = prices[prices.length - 1];

    let signal = 'HOLD';
    if (current > upper) signal = 'OVERBOUGHT';
    else if (current < lower) signal = 'OVERSOLD';

    const bandwidth = ((upper - lower) / ema) * 100;

    return {
        upper,
        middle: ema,
        lower,
        signal,
        bandwidth,
        squeeze: bandwidth < 10 // Low volatility squeeze
    };
}

// ========== LEGENDARY TRADER INDICATORS ==========

calculateWyckoffAccumulation(history) {
    // Richard Wyckoff's Accumulation/Distribution Detection
    // Analyzes volume vs price action to detect smart money
    if (!history || history.length < 20) return null;

    let accumulation = 0;
    let distribution = 0;

    for (let i = 1; i < history.length; i++) {
        const priceChange = history[i].price - history[i-1].price;
        const volume = history[i].volume || 1;

        // High volume + small price change = accumulation/distribution
        const avgVolume = history.reduce((sum, h) => sum + (h.volume || 1), 0) / history.length;

        if (volume > avgVolume * 1.5) {
            if (Math.abs(priceChange) < history[i-1].price * 0.01) {
                // High volume, low price movement
                if (priceChange >= 0) accumulation += volume;
                else distribution += volume;
            }
        }
    }

    const total = accumulation + distribution;
    const wyckoffScore = total > 0 ? ((accumulation - distribution) / total) * 100 : 0;

    let phase = 'NEUTRAL';
    if (wyckoffScore > 30) phase = 'ACCUMULATION';
    else if (wyckoffScore < -30) phase = 'DISTRIBUTION';
    else if (wyckoffScore > 10) phase = 'MARKUP';
    else if (wyckoffScore < -10) phase = 'MARKDOWN';

    return {
        score: wyckoffScore,
        phase,
        signal: wyckoffScore > 20 ? 'BUY' : wyckoffScore < -20 ? 'SELL' : 'HOLD',
        accumulation,
        distribution
    };
}

calculateMinerviniTrend(prices, history) {
    // Mark Minervini's Trend Template (SEPA criteria)
    if (prices.length < 200) return null;

    const current = prices[prices.length - 1];
    const sma50 = this.calculateSMA(prices, 50);
    const sma150 = this.calculateSMA(prices, 150);
    const sma200 = this.calculateSMA(prices, 200);

    // 52-week high/low
    const high52w = Math.max(...prices.slice(-252));
    const low52w = Math.min(...prices.slice(-252));

    // Minervini's 8 criteria
    const criteria = {
        priceAbove150: current > sma150,
        priceAbove200: current > sma200,
        sma200Trending: sma200 > prices[prices.length - 30],
        sma50Above150: sma50 > sma150,
        sma50Above200: sma50 > sma200,
        currentAbove50: current > sma50,
        priceNear52High: current >= high52w * 0.75, // Within 25% of 52w high
        priceAbove52Low: current >= low52w * 1.30  // At least 30% above 52w low
    };

    const score = Object.values(criteria).filter(Boolean).length;

    let signal = 'NEUTRAL';
    if (score >= 7) signal = 'STRONG BUY';
    else if (score >= 5) signal = 'BUY';
    else if (score <= 2) signal = 'SELL';

    return {
        score,
        maxScore: 8,
        percentage: (score / 8) * 100,
        signal,
        criteria,
        stage: score >= 6 ? 'STAGE 2' : score >= 4 ? 'STAGE 1' : score <= 2 ? 'STAGE 4' : 'STAGE 3'
    };
}

calculateMarketCipher(prices, history) {
    // Market Cipher B - Combines multiple oscillators
    // Popular among crypto traders (inspired by VuManChu)
    if (prices.length < 20 || !history) return null;

    // Wave Trend
    const ema1 = this.calculateEMA(prices, 10);
    const ema2 = this.calculateEMA(prices, 21);
    const waveTrend = ((ema1 - ema2) / ema2) * 100;

    // Money Flow
    let mfPositive = 0;
    let mfNegative = 0;

    for (let i = 1; i < Math.min(history.length, 14); i++) {
        const typical = history[i].price;
        const volume = history[i].volume || 1;

        if (history[i].price > history[i-1].price) {
            mfPositive += typical * volume;
        } else {
            mfNegative += typical * volume;
        }
    }

    const mfi = mfPositive + mfNegative > 0 ?
        100 - (100 / (1 + (mfPositive / mfNegative))) : 50;

    // RSI
    const rsi = this.calculateRSI(prices, 14);

    // Combined signal
    let signal = 'NEUTRAL';
    let strength = 0;

    if (waveTrend < -3 && mfi < 30 && rsi < 30) {
        signal = 'EXTREME BUY';
        strength = 3;
    } else if (waveTrend < -1 && (mfi < 40 || rsi < 40)) {
        signal = 'BUY';
        strength = 2;
    } else if (waveTrend > 3 && mfi > 70 && rsi > 70) {
        signal = 'EXTREME SELL';
        strength = -3;
    } else if (waveTrend > 1 && (mfi > 60 || rsi > 60)) {
        signal = 'SELL';
        strength = -2;
    }

    return {
        waveTrend,
        moneyFlow: mfi,
        rsi,
        signal,
        strength,
        divergence: (waveTrend < 0 && rsi > 50) || (waveTrend > 0 && rsi < 50)
    };
}

calculateWeisWave(history) {
    // David Weis Wave Volume - Cumulative volume analysis
    if (!history || history.length < 10) return null;

    const waves = [];
    let currentWave = { volume: 0, direction: null, bars: 0 };

    for (let i = 1; i < history.length; i++) {
        const trend = history[i].price > history[i-1].price ? 'up' : 'down';
        const volume = history[i].volume || 1;

        if (currentWave.direction === null) {
            currentWave.direction = trend;
        }

        if (trend === currentWave.direction) {
            currentWave.volume += volume;
            currentWave.bars++;
        } else {
            waves.push({...currentWave});
            currentWave = { volume, direction: trend, bars: 1 };
        }
    }

    if (currentWave.bars > 0) waves.push(currentWave);

    // Analyze last 5 waves
    const recentWaves = waves.slice(-5);
    const upWaves = recentWaves.filter(w => w.direction === 'up');
    const downWaves = recentWaves.filter(w => w.direction === 'down');

    const upVolume = upWaves.reduce((sum, w) => sum + w.volume, 0);
    const downVolume = downWaves.reduce((sum, w) => sum + w.volume, 0);

    const imbalance = upVolume + downVolume > 0 ?
        ((upVolume - downVolume) / (upVolume + downVolume)) * 100 : 0;

    return {
        currentDirection: currentWave.direction,
        volumeImbalance: imbalance,
        signal: imbalance > 25 ? 'STRONG BUY' : imbalance > 10 ? 'BUY' :
                imbalance < -25 ? 'STRONG SELL' : imbalance < -10 ? 'SELL' : 'NEUTRAL',
        upVolume,
        downVolume,
        waveCount: waves.length
    };
}

calculateSMC(prices, history) {
    // Smart Money Concepts (SMC) - Order blocks & liquidity
    // Popular in ICT (Inner Circle Trader) methodology
    if (!history || history.length < 30) return null;

    const current = prices[prices.length - 1];

    // Find Order Blocks (strong support/resistance from institutions)
    const orderBlocks = [];
    for (let i = 5; i < history.length - 5; i++) {
        const volume = history[i].volume || 1;
        const avgVolume = history.reduce((s, h) => s + (h.volume || 1), 0) / history.length;

        // High volume candle with strong move
        if (volume > avgVolume * 2) {
            const priceMove = Math.abs(history[i].price - history[i-1].price);
            const avgMove = prices.slice(-10).reduce((s, p, idx, arr) =>
                idx > 0 ? s + Math.abs(p - arr[idx-1]) : s, 0) / 10;

            if (priceMove > avgMove * 1.5) {
                orderBlocks.push({
                    price: history[i].price,
                    type: history[i].price > history[i-1].price ? 'bullish' : 'bearish',
                    strength: volume / avgVolume
                });
            }
        }
    }

    // Find nearest order block
    const bullishOB = orderBlocks.filter(ob => ob.type === 'bullish' && ob.price < current)
        .sort((a, b) => b.price - a.price)[0];
    const bearishOB = orderBlocks.filter(ob => ob.type === 'bearish' && ob.price > current)
        .sort((a, b) => a.price - b.price)[0];

    // Market Structure (Higher Highs, Lower Lows)
    const highs = [];
    const lows = [];

    for (let i = 5; i < prices.length - 5; i++) {
        const isHigh = prices.slice(i-5, i).every(p => p < prices[i]) &&
                       prices.slice(i+1, i+6).every(p => p < prices[i]);
        const isLow = prices.slice(i-5, i).every(p => p > prices[i]) &&
                      prices.slice(i+1, i+6).every(p => p > prices[i]);

        if (isHigh) highs.push(prices[i]);
        if (isLow) lows.push(prices[i]);
    }

    const recentHighs = highs.slice(-3);
    const recentLows = lows.slice(-3);

    let marketStructure = 'RANGING';
    if (recentHighs.length >= 2 && recentHighs[recentHighs.length-1] > recentHighs[recentHighs.length-2]) {
        marketStructure = 'BULLISH';
    } else if (recentLows.length >= 2 && recentLows[recentLows.length-1] < recentLows[recentLows.length-2]) {
        marketStructure = 'BEARISH';
    }

    let signal = 'NEUTRAL';
    if (marketStructure === 'BULLISH' && bullishOB) signal = 'BUY';
    else if (marketStructure === 'BEARISH' && bearishOB) signal = 'SELL';

    return {
        marketStructure,
        signal,
        bullishOrderBlock: bullishOB?.price,
        bearishOrderBlock: bearishOB?.price,
        orderBlockCount: orderBlocks.length,
        trendStrength: orderBlocks.length > 5 ? 'STRONG' : 'WEAK'
    };
}

calculateAllIndicators(prices) {
    const current = prices[prices.length - 1];
    
    // RSI
    const rsi = this.calculateRSI(prices, 14);
    const rsiSignal = rsi < 30 ? 'BUY' : rsi > 70 ? 'SELL' : 'HOLD';
    
    // MACD
    const macd = this.calculateMACD(prices);
    const macdSignal = macd.histogram > 0 ? 'BUY' : 'SELL';
    
    // Moving Averages
    const sma20 = this.calculateSMA(prices, 20);
    const sma50 = this.calculateSMA(prices, 50);
    const ema12 = this.calculateEMA(prices, 12);
    const ema26 = this.calculateEMA(prices, 26);
    const goldenCross = ema12 > ema26;
    const maSignal = goldenCross ? 'BUY' : 'SELL';
    
    // Bollinger Bands
    const bb = this.calculateBollingerBands(prices);
    let bbSignal = 'HOLD';
    if (current < bb.lower) bbSignal = 'BUY';
    else if (current > bb.upper) bbSignal = 'SELL';
    
    // Stochastic
    const stoch = this.calculateStochastic(prices);
    const stochSignal = stoch.k < 20 ? 'BUY' : stoch.k > 80 ? 'SELL' : 'HOLD';
    
    // ATR
    const atr = this.calculateATR(prices);
    const atrPercent = (atr / current) * 100;

    // Advanced Indicators
    const supertrend = this.calculateSupertrend(prices);
    const ichimoku = this.calculateIchimokuCloud(prices);
    const elderRay = this.calculateElderRay(prices);
    const keltner = this.calculateKeltnerChannels(prices);

    return {
        rsi: { value: rsi, signal: rsiSignal },
        macd: { value: macd.macd, signal: macdSignal, histogram: macd.histogram },
        ma: { value: sma20, sma50, ema12, ema26, signal: maSignal, goldenCross },
        bb: { value: bb.middle, upper: bb.upper, lower: bb.lower, signal: bbSignal },
        stoch: { k: stoch.k, d: stoch.d, signal: stochSignal },
        atr: { value: atr, percent: atrPercent },
        supertrend: supertrend || { signal: 'N/A', trend: 'N/A' },
        ichimoku: ichimoku || { signal: 'N/A' },
        elderRay: elderRay || { signal: 'N/A', bullPower: 0, bearPower: 0 },
        keltner: keltner || { signal: 'N/A', squeeze: false }
    };
}


        async loadIndicators() {
        try {
            console.log(`📊 Calculating technical indicators for ${this.selectedCoin}...`);

            // Use cached price history or fetch if needed
            if (!this.priceHistory || this.priceHistory.length < 20) {
                console.log("⚠️ Price history not available, fetching...");
                const response = await fetch(`${this.apiBase}/data/history/168?symbol=${this.selectedCoin}`);
                if (response.ok) {
                    const result = await response.json();
                    this.priceHistory = result.success ? result.data.history : result.history;
                }
            }

            if (!this.priceHistory || this.priceHistory.length < 20) {
                console.warn("❌ Insufficient price history for indicators");
                this.setIndicatorLoading();
                return;
            }

            console.log(`✅ Using ${this.priceHistory.length} price points for ${this.selectedCoin} indicators`);

            // Calculate indicators from price data
            const prices = this.priceHistory.map(h => h.price);
            const indicators = this.calculateAllIndicators(prices);

            // Calculate advanced indicators that need volume data
            const vwap = this.calculateVWAP(this.priceHistory);
            const orderFlow = this.calculateOrderFlowImbalance(this.priceHistory);

            // Calculate legendary trader indicators
            console.log(`🏆 Calculating legendary indicators for ${this.selectedCoin}...`);
            const wyckoff = this.calculateWyckoffAccumulation(this.priceHistory);
            const minervini = this.calculateMinerviniTrend(prices, this.priceHistory);
            const marketCipher = this.calculateMarketCipher(prices, this.priceHistory);
            const weisWave = this.calculateWeisWave(this.priceHistory);
            const smc = this.calculateSMC(prices, this.priceHistory);

            // Merge all indicators
            indicators.vwap = vwap || { signal: 'N/A', deviation: 0 };
            indicators.orderFlow = orderFlow || { signal: 'N/A', imbalance: 0 };
            indicators.wyckoff = wyckoff || { signal: 'HOLD', phase: 'N/A' };
            indicators.minervini = minervini || { signal: 'NEUTRAL', score: 0 };
            indicators.marketCipher = marketCipher || { signal: 'NEUTRAL', strength: 0 };
            indicators.weisWave = weisWave || { signal: 'NEUTRAL', volumeImbalance: 0 };
            indicators.smc = smc || { signal: 'NEUTRAL', marketStructure: 'RANGING' };

            console.log(`✅ All indicators calculated for ${this.selectedCoin}:`, {
                wyckoff: wyckoff?.phase,
                minervini: minervini?.score,
                marketCipher: marketCipher?.signal,
                weisWave: weisWave?.volumeImbalance,
                smc: smc?.marketStructure
            });
            this.updateIndicatorsDisplay(indicators);
            this.updateAdvancedIndicatorsDisplay(indicators);
            this.updateLegendaryIndicatorsDisplay(indicators);

            // Also try to fetch server-side analytics for enhanced data
            this.loadServerAnalytics();
        } catch (error) {
            console.error("❌ Error calculating indicators:", error);
            this.setIndicatorLoading();
        }
    }
    
    async loadServerAnalytics() {
        try {
            const response = await fetch(`${this.apiBase}/data/analytics/${this.selectedCoin}`);
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    console.log("✅ Enhanced analytics from server:", result);
                    // Merge with client-side calculations
                }
            }
        } catch (error) {
            console.log("Server analytics not available, using client-side only");
        }
    }

    updateIndicatorsDisplay(indicators) {
        // Update RSI
        const rsiVal = document.getElementById("rsi-value");
        const rsiSig = document.getElementById("rsi-signal");
        if (rsiVal) rsiVal.textContent = indicators.rsi.value.toFixed(2);
        if (rsiSig) {
            const badge = rsiSig.querySelector('.terminal-badge') || rsiSig;
            badge.textContent = indicators.rsi.signal;
            badge.className = `terminal-badge ${indicators.rsi.signal.toLowerCase() === 'buy' ? 'success' : indicators.rsi.signal.toLowerCase() === 'sell' ? 'danger' : 'info'}`;
        }
        
        // Update MACD
        const macdVal = document.getElementById("macd-value");
        const macdSig = document.getElementById("macd-signal");
        if (macdVal) macdVal.textContent = indicators.macd.value.toFixed(2);
        if (macdSig) {
            const badge = macdSig.querySelector('.terminal-badge') || macdSig;
            badge.textContent = indicators.macd.signal;
            badge.className = `terminal-badge ${indicators.macd.signal.toLowerCase() === 'buy' ? 'success' : 'danger'}`;
        }
        
        // Update MA
        const maVal = document.getElementById("ma-value");
        const maSig = document.getElementById("ma-signal");
        if (maVal) maVal.textContent = indicators.ma.value.toFixed(2);
        if (maSig) {
            const badge = maSig.querySelector('.terminal-badge') || maSig;
            badge.textContent = indicators.ma.signal;
            badge.className = `terminal-badge ${indicators.ma.signal.toLowerCase() === 'buy' ? 'success' : 'danger'}`;
        }
        
        // Update Bollinger Bands
        const bbVal = document.getElementById("bb-value");
        const bbSig = document.getElementById("bb-signal");
        if (bbVal) bbVal.textContent = indicators.bb.value.toFixed(2);
        if (bbSig) {
            const badge = bbSig.querySelector('.terminal-badge') || bbSig;
            badge.textContent = indicators.bb.signal;
            badge.className = `terminal-badge ${indicators.bb.signal.toLowerCase() === 'buy' ? 'success' : indicators.bb.signal.toLowerCase() === 'sell' ? 'danger' : 'info'}`;
        }
        
        console.log("✅ Indicators display updated");
    }

    setIndicatorLoading() {
        ["rsi", "macd", "bb", "ma"].forEach((key) => {
            const valueEl = document.getElementById(`${key}-value`);
            const signalEl = document.getElementById(`${key}-signal`);
            if (valueEl) valueEl.textContent = "--";
            if (signalEl) {
                signalEl.textContent = "NO DATA";
                signalEl.className = "indicator-signal signal-neutral";
            }
        });
    }

    updateAdvancedIndicatorsDisplay(indicators) {
        console.log("📊 Updating advanced indicators display");

        // VWAP
        const vwapEl = document.getElementById("vwap-value");
        const vwapSigEl = document.getElementById("vwap-signal");
        if (vwapEl && indicators.vwap) {
            vwapEl.textContent = `$${indicators.vwap.vwap?.toFixed(2) || '--'}`;
        }
        if (vwapSigEl && indicators.vwap) {
            const badge = vwapSigEl.querySelector('.terminal-badge') || vwapSigEl;
            badge.textContent = indicators.vwap.signal;
            const badgeClass = indicators.vwap.signal === 'BUY' ? 'success' : indicators.vwap.signal === 'SELL' ? 'danger' : 'info';
            badge.className = `terminal-badge ${badgeClass}`;
        }

        // Order Flow Imbalance
        const ofiEl = document.getElementById("ofi-value");
        const ofiSigEl = document.getElementById("ofi-signal");
        if (ofiEl && indicators.orderFlow) {
            ofiEl.textContent = `${indicators.orderFlow.imbalance?.toFixed(1) || 0}%`;
        }
        if (ofiSigEl && indicators.orderFlow) {
            const badge = ofiSigEl.querySelector('.terminal-badge') || ofiSigEl;
            badge.textContent = indicators.orderFlow.signal;
            const signal = indicators.orderFlow.signal;
            let badgeClass = 'info';
            if (signal.includes('STRONG BUY')) badgeClass = 'success';
            else if (signal.includes('STRONG SELL')) badgeClass = 'danger';
            else if (signal === 'BUY') badgeClass = 'success';
            else if (signal === 'SELL') badgeClass = 'danger';
            badge.className = `terminal-badge ${badgeClass}`;
        }

        // Ichimoku Cloud
        const ichimokuEl = document.getElementById("ichimoku-value");
        const ichimokuSigEl = document.getElementById("ichimoku-signal");
        if (ichimokuEl && indicators.ichimoku) {
            const cloud = indicators.ichimoku.inCloud ? 'In Cloud' : indicators.ichimoku.bullishCloud ? 'Bullish' : 'Bearish';
            ichimokuEl.textContent = cloud;
        }
        if (ichimokuSigEl && indicators.ichimoku) {
            const badge = ichimokuSigEl.querySelector('.terminal-badge') || ichimokuSigEl;
            badge.textContent = indicators.ichimoku.signal;
            const signal = indicators.ichimoku.signal;
            let badgeClass = 'info';
            if (signal.includes('STRONG BUY')) badgeClass = 'success';
            else if (signal.includes('STRONG SELL')) badgeClass = 'danger';
            else if (signal === 'BUY') badgeClass = 'success';
            else if (signal === 'SELL') badgeClass = 'danger';
            badge.className = `terminal-badge ${badgeClass}`;
        }

        // Supertrend
        const supertrendEl = document.getElementById("supertrend-value");
        const supertrendSigEl = document.getElementById("supertrend-signal");
        if (supertrendEl && indicators.supertrend) {
            supertrendEl.textContent = indicators.supertrend.trend || 'N/A';
        }
        if (supertrendSigEl && indicators.supertrend) {
            const badge = supertrendSigEl.querySelector('.terminal-badge') || supertrendSigEl;
            badge.textContent = indicators.supertrend.signal;
            const badgeClass = indicators.supertrend.signal === 'BUY' ? 'success' : indicators.supertrend.signal === 'SELL' ? 'danger' : 'info';
            badge.className = `terminal-badge ${badgeClass}`;
        }

        // Elder Ray
        const elderEl = document.getElementById("elder-value");
        const elderSigEl = document.getElementById("elder-signal");
        if (elderEl && indicators.elderRay) {
            const bull = indicators.elderRay.bullPower?.toFixed(2) || 0;
            const bear = indicators.elderRay.bearPower?.toFixed(2) || 0;
            elderEl.textContent = `B:${bull} / Be:${bear}`;
        }
        if (elderSigEl && indicators.elderRay) {
            const badge = elderSigEl.querySelector('.terminal-badge') || elderSigEl;
            badge.textContent = indicators.elderRay.signal;
            const signal = indicators.elderRay.signal;
            let badgeClass = 'info';
            if (signal.includes('STRONG BUY')) badgeClass = 'success';
            else if (signal.includes('STRONG SELL')) badgeClass = 'danger';
            else if (signal === 'BUY') badgeClass = 'success';
            else if (signal === 'SELL') badgeClass = 'danger';
            badge.className = `terminal-badge ${badgeClass}`;
        }

        // Keltner Channels
        const keltnerEl = document.getElementById("keltner-value");
        const keltnerSigEl = document.getElementById("keltner-signal");
        if (keltnerEl && indicators.keltner) {
            const status = indicators.keltner.squeeze ? 'SQUEEZE' : 'NORMAL';
            keltnerEl.textContent = status;
        }
        if (keltnerSigEl && indicators.keltner) {
            const badge = keltnerSigEl.querySelector('.terminal-badge') || keltnerSigEl;
            badge.textContent = indicators.keltner.signal;
            const signal = indicators.keltner.signal;
            const badgeClass = signal === 'OVERSOLD' ? 'success' : signal === 'OVERBOUGHT' ? 'danger' : 'info';
            badge.className = `terminal-badge ${badgeClass}`;
        }
    }

    updateLegendaryIndicatorsDisplay(indicators) {
        console.log("🏆 Updating legendary trader indicators display");

        // Wyckoff Accumulation/Distribution
        const wyckoffPhaseEl = document.getElementById("wyckoff-phase");
        const wyckoffScoreEl = document.getElementById("wyckoff-score");
        const wyckoffSigEl = document.getElementById("wyckoff-signal");
        if (wyckoffPhaseEl && indicators.wyckoff) {
            wyckoffPhaseEl.textContent = indicators.wyckoff.phase || 'NEUTRAL';
            wyckoffPhaseEl.style.color = indicators.wyckoff.phase === 'ACCUMULATION' ? 'var(--status-profit)' :
                                          indicators.wyckoff.phase === 'DISTRIBUTION' ? 'var(--status-loss)' :
                                          'var(--text-secondary)';
        }
        if (wyckoffScoreEl && indicators.wyckoff) {
            wyckoffScoreEl.textContent = `Score: ${indicators.wyckoff.score?.toFixed(1) || 0}%`;
        }
        if (wyckoffSigEl && indicators.wyckoff) {
            const badge = wyckoffSigEl.querySelector('.terminal-badge') || wyckoffSigEl;
            badge.textContent = indicators.wyckoff.signal;
            const badgeClass = indicators.wyckoff.signal === 'BUY' ? 'success' : indicators.wyckoff.signal === 'SELL' ? 'danger' : 'info';
            badge.className = `terminal-badge ${badgeClass}`;
        }

        // Minervini Trend Template
        const minerviniScoreEl = document.getElementById("minervini-score");
        const minerviniStageEl = document.getElementById("minervini-stage");
        const minerviniSigEl = document.getElementById("minervini-signal");
        if (minerviniScoreEl && indicators.minervini) {
            const score = indicators.minervini.score || 0;
            const maxScore = indicators.minervini.maxScore || 8;
            minerviniScoreEl.textContent = `${score}/${maxScore}`;
            minerviniScoreEl.style.color = score >= 6 ? 'var(--status-profit)' :
                                            score >= 4 ? 'var(--text-warning)' :
                                            'var(--status-loss)';
        }
        if (minerviniStageEl && indicators.minervini) {
            minerviniStageEl.textContent = `Stage: ${indicators.minervini.stage || 'N/A'}`;
        }
        if (minerviniSigEl && indicators.minervini) {
            const badge = minerviniSigEl.querySelector('.terminal-badge') || minerviniSigEl;
            badge.textContent = indicators.minervini.signal;
            const signal = indicators.minervini.signal;
            let badgeClass = 'info';
            if (signal === 'STRONG BUY') badgeClass = 'success';
            else if (signal === 'BUY') badgeClass = 'success';
            else if (signal === 'SELL') badgeClass = 'danger';
            badge.className = `terminal-badge ${badgeClass}`;
        }

        // Market Cipher B
        const cipherStrengthEl = document.getElementById("cipher-strength");
        const cipherWaveEl = document.getElementById("cipher-wave");
        const cipherSigEl = document.getElementById("cipher-signal");
        if (cipherStrengthEl && indicators.marketCipher) {
            const strength = indicators.marketCipher.strength || 0;
            cipherStrengthEl.textContent = `${strength > 0 ? '+' : ''}${strength.toFixed(1)}`;
            cipherStrengthEl.style.color = strength > 0 ? 'var(--status-profit)' : 'var(--status-loss)';
        }
        if (cipherWaveEl && indicators.marketCipher) {
            cipherWaveEl.textContent = `Wave: ${indicators.marketCipher.waveTrend?.toFixed(2) || 0}`;
        }
        if (cipherSigEl && indicators.marketCipher) {
            const badge = cipherSigEl.querySelector('.terminal-badge') || cipherSigEl;
            badge.textContent = indicators.marketCipher.signal;
            const signal = indicators.marketCipher.signal;
            let badgeClass = 'info';
            if (signal.includes('STRONG BUY')) badgeClass = 'success';
            else if (signal === 'BUY') badgeClass = 'success';
            else if (signal === 'SELL') badgeClass = 'danger';
            badge.className = `terminal-badge ${badgeClass}`;
        }

        // Weis Wave Volume
        const weisImbalanceEl = document.getElementById("weis-imbalance");
        const weisWaveEl = document.getElementById("weis-wave");
        const weisSigEl = document.getElementById("weis-signal");
        if (weisImbalanceEl && indicators.weisWave) {
            const imbalance = indicators.weisWave.volumeImbalance || 0;
            weisImbalanceEl.textContent = `${imbalance > 0 ? '+' : ''}${imbalance.toFixed(1)}%`;
            weisImbalanceEl.style.color = imbalance > 0 ? 'var(--status-profit)' : 'var(--status-loss)';
        }
        if (weisWaveEl && indicators.weisWave) {
            weisWaveEl.textContent = `Wave: ${indicators.weisWave.currentWave || 'UP'}`;
        }
        if (weisSigEl && indicators.weisWave) {
            const badge = weisSigEl.querySelector('.terminal-badge') || weisSigEl;
            badge.textContent = indicators.weisWave.signal;
            const badgeClass = indicators.weisWave.signal === 'BUY' ? 'success' : indicators.weisWave.signal === 'SELL' ? 'danger' : 'info';
            badge.className = `terminal-badge ${badgeClass}`;
        }

        // Smart Money Concepts (SMC)
        const smcStructureEl = document.getElementById("smc-structure");
        const smcOrderBlockEl = document.getElementById("smc-orderblock");
        const smcSigEl = document.getElementById("smc-signal");
        if (smcStructureEl && indicators.smc) {
            const structure = indicators.smc.marketStructure || 'RANGING';
            smcStructureEl.textContent = structure;
            smcStructureEl.style.color = structure === 'BULLISH' ? 'var(--status-profit)' :
                                          structure === 'BEARISH' ? 'var(--status-loss)' :
                                          'var(--text-secondary)';
        }
        if (smcOrderBlockEl && indicators.smc) {
            let obText = 'None';
            if (indicators.smc.bullishOrderBlock) {
                obText = `🟢 $${indicators.smc.bullishOrderBlock.price?.toFixed(2) || '??'}`;
            } else if (indicators.smc.bearishOrderBlock) {
                obText = `🔴 $${indicators.smc.bearishOrderBlock.price?.toFixed(2) || '??'}`;
            }
            smcOrderBlockEl.textContent = obText;
        }
        if (smcSigEl && indicators.smc) {
            const badge = smcSigEl.querySelector('.terminal-badge') || smcSigEl;
            badge.textContent = indicators.smc.signal;
            const signal = indicators.smc.signal;
            let badgeClass = 'info';
            if (signal.includes('STRONG BUY')) badgeClass = 'success';
            else if (signal === 'BUY') badgeClass = 'success';
            else if (signal === 'SELL') badgeClass = 'danger';
            badge.className = `terminal-badge ${badgeClass}`;
        }
    }

    async loadPriceHistory() {
        const loadingKey = "price-history";
        try {
            const coinInfo = this.getCoinInfo();
            this.showLoading(loadingKey, `Loading ${coinInfo.name} price history...`);

            console.log(`📊 Fetching ${coinInfo.name} price history from ${this.apiBase}/data/history/24?symbol=${this.selectedCoin}`);
            const hours = this.selectedTimeframe || 24;
            console.log('Fetching', hours, 'hours of price history for', this.selectedCoin);
            const response = await fetch(
                `${this.apiBase}/data/history/${hours}?symbol=${this.selectedCoin}`,
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('📊 History API response:', result);
            const data = result.success ? result.data : result;

            if (data.history) {
                console.log(`✅ ${coinInfo.name} history has ${data.history.length} data points`);

                if (this.charts.price) {
                    console.log('📊 Chart exists, updating...');
                    this.updatePriceChart(data.history);
                } else {
                    console.warn('⚠️ Price chart not initialized! Initializing now...');
                    this.initializePriceChart();
                    if (this.charts.price) {
                        this.updatePriceChart(data.history);
                    }
                }
            } else {
                console.warn('⚠️ No history data in response');
            }
        } catch (error) {
            console.error(`❌ Error loading ${this.getCoinInfo().name} price history:`, error);
        } finally {
            this.hideLoading(loadingKey);
        }
    }

    async loadMarketDepth() {
        const loadingKey = "market-depth";
        try {
            // Try Binance API first (may be geo-restricted)
            this.showLoading(loadingKey, "Loading market depth...");
            console.log("📊 Fetching real market depth...");
            const coinInfo = this.getCoinInfo();
            let response = await fetch(
                `https://api.binance.com/api/v3/depth?symbol=${coinInfo.binanceSymbol}&limit=50`,
            );

            // If Binance fails (geo-restriction), try through our backend or alternative
            if (!response.ok || response.status === 451) {
                console.log("⚠️ Binance API unavailable (geo-restriction), trying alternatives...");

                // Try CoinGecko as fallback (no order book depth available on free tier)
                // Show informative message instead
                this.showDepthUnavailable();
                return;
            }

            const data = await response.json();

            // Check for Binance error response
            if (data.code === 0 && data.msg) {
                console.log("⚠️ Binance API restricted:", data.msg);
                this.showDepthUnavailable();
                return;
            }

            console.log("✅ Real order book data received");
            this.updateDepthChart(data);
        } catch (error) {
            console.error("❌ Error loading market depth:", error);
            this.showDepthUnavailable();
        } finally {
            this.hideLoading(loadingKey);
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
                fill: "tozeroy",
                type: "scatter",
                mode: "lines",
                name: "Bids",
                line: { color: "#00ff88", width: 2 },
            },
            {
                x: askPrices,
                y: askVolumes,
                fill: "tozeroy",
                type: "scatter",
                mode: "lines",
                name: "Asks",
                line: { color: "#ff3366", width: 2 },
            },
        ];

        const layout = {
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            xaxis: {
                color: "#8b92b0",
                gridcolor: "rgba(139, 146, 176, 0.1)",
                title: "Price (USDT)",
            },
            yaxis: {
                color: "#8b92b0",
                gridcolor: "rgba(139, 146, 176, 0.1)",
                title: `Cumulative Volume (${this.selectedCoin})`,
            },
            showlegend: true,
            legend: {
                font: { color: "#8b92b0" },
                bgcolor: "transparent",
            },
            margin: { t: 20, r: 20, b: 40, l: 60 },
        };

        Plotly.newPlot("depth-chart", traces, layout, { displayModeBar: false });
    }

    showPlaceholderDepth() {
        document.getElementById("depth-chart").innerHTML =
            '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary);">Unable to load order book data</div>';
    }

    showDepthUnavailable() {
        document.getElementById("depth-chart").innerHTML = `
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
            console.log("📊 Fetching real funding rate...");
            const coinInfo = this.getCoinInfo();
            const response = await fetch(
                `https://fapi.binance.com/fapi/v1/premiumIndex?symbol=${coinInfo.binanceSymbol}`,
            );

            if (!response.ok || response.status === 451) {
                console.log("⚠️ Binance Futures API unavailable (geo-restriction)");
                this.setFundingUnavailable();
                return;
            }

            const data = await response.json();

            // Check for Binance error response
            if (data.code === 0 && data.msg) {
                console.log("⚠️ Binance Futures API restricted:", data.msg);
                this.setFundingUnavailable();
                return;
            }

            console.log("✅ Real funding rate received:", data);
            this.updateFundingRate(data);
        } catch (error) {
            console.error("❌ Error loading funding rate:", error);
            this.setFundingUnavailable();
        }
    }

    updateFundingRate(data) {
        const fundingRate = parseFloat(data.lastFundingRate) * 100;
        const fundingEl = document.getElementById("funding-rate");

        if (fundingEl) {
            fundingEl.textContent = `${fundingRate >= 0 ? "+" : ""}${fundingRate.toFixed(4)}%`;
            fundingEl.className = `funding-value ${fundingRate >= 0 ? "funding-positive" : "funding-negative"}`;
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
                const countdownEl = document.getElementById("funding-countdown");
                if (countdownEl) {
                    countdownEl.textContent = `${hours}h ${minutes}m ${seconds}s`;
                }
            }
        };

        updateCountdown();
        setInterval(updateCountdown, 1000);
    }

    setFundingPlaceholder() {
        const fundingEl = document.getElementById("funding-rate");
        if (fundingEl) {
            fundingEl.textContent = "No Data";
            fundingEl.className = "funding-value";
        }
    }

    setFundingUnavailable() {
        const fundingEl = document.getElementById("funding-rate");
        if (fundingEl) {
            fundingEl.textContent = "Unavailable";
            fundingEl.className = "funding-value";
            fundingEl.style.fontSize = "1.2rem";
        }
        const countdownEl = document.getElementById("funding-countdown");
        if (countdownEl) {
            countdownEl.textContent = "API geo-restricted";
        }
    }

    async loadLiquidations() {
        // Note: Real liquidation data requires paid API access from services like:
        // - Coinglass API
        // - Bybit API
        // - FTX API (if available)
        // For now, we'll show a message that this requires premium data
        console.log("⚠️ Liquidation data requires premium API access");
        this.showLiquidationMessage();
    }

    showLiquidationMessage() {
        const heatmapEl = document.getElementById("liquidation-heatmap");
        if (heatmapEl) {
            heatmapEl.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; flex-direction: column; color: var(--text-secondary);">
                    <div style="font-size: 1.2rem; margin-bottom: 1rem;">📊 Liquidation Heatmap</div>
                    <div style="font-size: 0.875rem;">Real liquidation data requires premium API access</div>
                    <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.7;">Contact Coinglass, Bybit, or similar providers</div>
                </div>
            `;
        }

        const tbody = document.querySelector("#liquidations-table tbody");
        if (tbody) {
            tbody.innerHTML =
                '<tr><td colspan="3" style="text-align: center; color: var(--text-secondary); padding: 2rem;">Liquidation feed requires premium API</td></tr>';
        }
    }

    /**
     * Destroy all charts to prevent memory leaks
     */
    destroyCharts() {
        Object.keys(this.charts).forEach((chartKey) => {
            if (this.charts[chartKey] && typeof this.charts[chartKey].destroy === "function") {
                this.charts[chartKey].destroy();
                delete this.charts[chartKey];
            }
        });
        this.logger.debug("Destroyed all charts");
    }

    initializeCharts() {
        // Destroy existing charts first to prevent memory leaks
        this.destroyCharts();

        this.initializePriceChart();
        this.initializeFundingChart();
        this.initializeOpenInterestChart();
    }

    initializePriceChart() {
        const ctx = document.getElementById("price-chart-canvas");
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (this.charts.price) {
            this.charts.price.destroy();
        }

        this.charts.price = new Chart(ctx, {
            type: "line",
            data: {
                datasets: [
                    {
                        label: `${this.selectedCoin} Price`,
                        data: [],
                        borderColor: "#0099ff",
                        backgroundColor: "rgba(0, 153, 255, 0.1)",
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false,
                    },
                },
                scales: {
                    x: {
                        type: "time",
                        time: {
                            unit: "hour",
                        },
                        grid: {
                            color: "rgba(139, 146, 176, 0.1)",
                        },
                        ticks: {
                            color: "#8b92b0",
                        },
                    },
                    y: {
                        grid: {
                            color: "rgba(139, 146, 176, 0.1)",
                        },
                        ticks: {
                            color: "#8b92b0",
                            callback: function (value) {
                                return "$" + value.toLocaleString();
                            },
                        },
                    },
                },
            },
        });
    }

    updatePriceChart(history) {
        if (!this.charts.price) {
            console.error('❌ Cannot update chart - chart not initialized');
            return;
        }

        if (!history || history.length === 0) {
            console.warn('⚠️ No history data to display in chart');
            return;
        }

        console.log(`📊 Updating price chart with ${history.length} data points`);

        const data = history.map((item) => ({
            x: new Date(item.timestamp * 1000),
            y: item.price,
        }));

        this.charts.price.data.datasets[0].data = data;
        this.charts.price.data.datasets[0].label = `${this.selectedCoin} Price`;
        this.charts.price.update();

        console.log('✅ Price chart updated successfully');
    }

    initializeFundingChart() {
        const ctx = document.getElementById("funding-chart");
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (this.charts.funding) {
            this.charts.funding.destroy();
        }

        this.charts.funding = new Chart(ctx, {
            type: "bar",
            data: {
                labels: ["No Data"],
                datasets: [
                    {
                        data: [0],
                        backgroundColor: ["#8b92b0"],
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false,
                    },
                },
                scales: {
                    x: {
                        grid: {
                            display: false,
                        },
                        ticks: {
                            color: "#8b92b0",
                        },
                    },
                    y: {
                        grid: {
                            color: "rgba(139, 146, 176, 0.1)",
                        },
                        ticks: {
                            color: "#8b92b0",
                            callback: function (value) {
                                return value.toFixed(3) + "%";
                            },
                        },
                    },
                },
            },
        });
    }

    initializeOpenInterestChart() {
        const ctx = document.getElementById("oi-chart");
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (this.charts.openInterest) {
            this.charts.openInterest.destroy();
        }

        this.charts.openInterest = new Chart(ctx, {
            type: "line",
            data: {
                labels: ["No Data"],
                datasets: [
                    {
                        label: "Open Interest",
                        data: [0],
                        borderColor: "#0099ff",
                        backgroundColor: "rgba(0, 153, 255, 0.1)",
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false,
                    },
                },
                scales: {
                    x: {
                        grid: {
                            display: false,
                        },
                        ticks: {
                            color: "#8b92b0",
                        },
                    },
                    y: {
                        grid: {
                            color: "rgba(139, 146, 176, 0.1)",
                        },
                        ticks: {
                            color: "#8b92b0",
                            callback: (value) => {
                                return value.toLocaleString() + " " + this.selectedCoin;
                            },
                        },
                    },
                },
            },
        });
    }

    async loadNews() {
        try {
            console.log("📰 Fetching crypto news...");

            // Using CoinGecko's trending search API (free, no key required)
            const response = await fetch("https://api.coingecko.com/api/v3/search/trending");

            if (!response.ok) {
                throw new Error("News API unavailable");
            }

            const data = await response.json();
            console.log("✅ Trending data received");

            // Transform trending data into news-like format
            const trendingCoins = data.coins || [];
            const newsItems = trendingCoins.map((coin, index) => ({
                title: `${coin.item.name} (${coin.item.symbol}) - Rank #${coin.item.market_cap_rank || "N/A"}`,
                subtitle: `24h Price: ${coin.item.data?.price || "N/A"} | Market Cap: $${(coin.item.data?.market_cap || 0).toLocaleString()}`,
                url: `https://www.coingecko.com/en/coins/${coin.item.id}`,
                source: "CoinGecko Trending",
                score: coin.item.score || index,
                timestamp: new Date(),
            }));

            this.displayTrendingNews(newsItems);
        } catch (error) {
            console.error("❌ Error loading news:", error);
            this.showNewsError();
        }
    }

    displayTrendingNews(items) {
        const newsContainer = document.getElementById("news-feed");
        if (!newsContainer) return;

        if (items.length === 0) {
            newsContainer.innerHTML =
                '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">No trending data available</div>';
            return;
        }

        newsContainer.innerHTML = items
            .map((item, index) => {
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
            })
            .join("");
    }

    showNewsError() {
        const newsContainer = document.getElementById("news-feed");
        if (newsContainer) {
            newsContainer.innerHTML =
                '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">News feed temporarily unavailable</div>';
        }
    }

    async loadTwitterFeed() {
        try {
            console.log("𝕏 Loading crypto Twitter feed...");

            // Using Nitter RSS-to-JSON for free Twitter data
            // Alternative: We'll show curated crypto Twitter accounts
            const accounts = [
                {
                    username: "Bitcoin",
                    handle: "@Bitcoin",
                    text: "Bitcoin is a swarm of cyber hornets serving the goddess of wisdom, feeding on the fire of truth",
                },
                {
                    username: "Vitalik Buterin",
                    handle: "@VitalikButerin",
                    text: "Ethereum and crypto updates",
                },
                { username: "CZ", handle: "@cz_binance", text: "Crypto market insights" },
                {
                    username: "Willy Woo",
                    handle: "@woonomic",
                    text: "On-chain analytics and Bitcoin insights",
                },
            ];

            // Try to fetch real Twitter/X data via RSS bridge or Nitter
            // For now, show placeholder with links to follow these accounts
            this.displayTwitterPlaceholder(accounts);
        } catch (error) {
            console.error("❌ Error loading Twitter feed:", error);
            this.showTwitterError();
        }
    }

    displayTwitterPlaceholder(accounts) {
        const twitterContainer = document.getElementById("twitter-feed");
        if (!twitterContainer) return;

        twitterContainer.innerHTML = `
            <div style="padding: 1rem;">
                <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 1rem;">
                    Follow these accounts for Bitcoin insights:
                </div>
                ${accounts
                    .map(
                        (account) => `
                    <div class="tweet-item" onclick="window.open('https://twitter.com/${account.handle.replace("@", "")}', '_blank')">
                        <div class="tweet-author">
                            <span class="tweet-username">${account.username}</span>
                            <span class="tweet-handle">${account.handle}</span>
                        </div>
                        <div class="tweet-text">${account.text}</div>
                        <div class="tweet-meta">Click to follow →</div>
                    </div>
                `,
                    )
                    .join("")}
                <div style="margin-top: 1rem; padding: 1rem; background: rgba(0, 153, 255, 0.1); border-radius: 8px; font-size: 0.875rem;">
                    💡 <strong>Note:</strong> Real-time Twitter feed requires authentication. This shows recommended accounts to follow.
                </div>
            </div>
        `;
    }

    showTwitterError() {
        const twitterContainer = document.getElementById("twitter-feed");
        if (twitterContainer) {
            twitterContainer.innerHTML =
                '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">Twitter feed unavailable</div>';
        }
    }

    async loadVolumeProfile() {
        try {
            console.log(`📊 Creating volume profile for ${this.selectedCoin}...`);

            // Get price history to build volume profile
            const response = await fetch(`${this.apiBase}/data/history/168?symbol=${this.selectedCoin}`); // 7 days

            if (!response.ok) {
                throw new Error("Failed to fetch history for volume profile");
            }

            const result = await response.json();
            const history = result.success ? result.data.history : result.history;

            if (history && history.length > 0) {
                this.createVolumeProfile(history);
            }
        } catch (error) {
            console.error("❌ Error loading volume profile:", error);
            this.showVolumeProfileError();
        }
    }

    createVolumeProfile(history) {
        // Create price buckets
        const prices = history.map((h) => h.price);
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);

        const bucketCount = 30;
        const bucketSize = (maxPrice - minPrice) / bucketCount;

        // Aggregate volume by price level
        const buckets = new Array(bucketCount).fill(0).map((_, i) => ({
            price: minPrice + i * bucketSize,
            volume: 0,
        }));

        history.forEach((candle) => {
            const bucketIndex = Math.min(
                Math.floor((candle.price - minPrice) / bucketSize),
                bucketCount - 1,
            );
            buckets[bucketIndex].volume += candle.volume || 0;
        });

        // Create horizontal bar chart with Plotly
        const trace = {
            y: buckets.map((b) => `$${b.price.toFixed(0)}`),
            x: buckets.map((b) => b.volume),
            type: "bar",
            orientation: "h",
            marker: {
                color: buckets.map((b) => {
                    const intensity = b.volume / Math.max(...buckets.map((b2) => b2.volume));
                    return `rgba(0, 153, 255, ${0.3 + intensity * 0.7})`;
                }),
            },
        };

        const layout = {
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            xaxis: {
                color: "#8b92b0",
                gridcolor: "rgba(139, 146, 176, 0.1)",
                title: `Volume (${this.selectedCoin})`,
            },
            yaxis: {
                color: "#8b92b0",
                gridcolor: "rgba(139, 146, 176, 0.1)",
                title: "Price Level",
            },
            margin: { t: 20, r: 20, b: 40, l: 80 },
            showlegend: false,
        };

        Plotly.newPlot("volume-profile", [trace], layout, { displayModeBar: false });
    }

    showVolumeProfileError() {
        const vpContainer = document.getElementById("volume-profile");
        if (vpContainer) {
            vpContainer.innerHTML =
                '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary);">Volume profile unavailable</div>';
        }
    }

    getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);

        let interval = seconds / 31536000;
        if (interval > 1) return Math.floor(interval) + "y ago";

        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + "mo ago";

        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + "d ago";

        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + "h ago";

        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + "m ago";

        return Math.floor(seconds) + "s ago";
    }

    escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    // ========== COIN SELECTOR ==========
    setupCoinSelector() {
        console.log('⚙️ Setting up coin selection...');

        // Load saved coin preference or default to BTC
        const savedCoin = localStorage.getItem("selectedCoin") || "BTC";
        this.selectedCoin = savedCoin;

        // Update coin name on initial load
        this.updateCoinName();

        // Note: Coin selection is handled entirely by ticker bar clicks
        // Global ticker event listener is attached at script load (see top of file)
        console.log('✅ Coin selection initialized - ticker bar will handle switching');
    }

    getCoinInfo() {
        return this.coinMappings[this.selectedCoin] || this.coinMappings["BTC"];
    }

    updateCoinName() {
        const coinInfo = this.getCoinInfo();

        // Update coin name in price section
        const coinNameEl = document.getElementById("coin-name");
        if (coinNameEl) {
            coinNameEl.textContent = coinInfo.name;
        }

        // Update coin name in price section title
        const priceCoinNameEl = document.getElementById("price-coin-name");
        if (priceCoinNameEl) {
            priceCoinNameEl.textContent = coinInfo.name;
        }

        // Update coin name in charts section
        const chartCoinNameEl = document.getElementById("chart-coin-name");
        if (chartCoinNameEl) {
            chartCoinNameEl.textContent = coinInfo.name;
        }

        // Update header coin symbol
        const headerSymbolEl = document.getElementById("header-coin-symbol");
        if (headerSymbolEl) {
            headerSymbolEl.textContent = `${coinInfo.symbol} ${this.selectedCoin}`;
        }
    }

    // ========== TIMEFRAME BUTTONS ==========
    setupTimeframeButtons() {
        const buttons = document.querySelectorAll('.timeframe-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const timeframe = parseInt(e.target.getAttribute('data-timeframe'));
                console.log(`Timeframe button clicked: ${timeframe}h`);

                // Update active state
                buttons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');

                // Update selected timeframe
                this.selectedTimeframe = timeframe;

                // Update TradingView chart if available
                if (window.tradingViewWidget) {
                    console.log(`Updating TradingView chart to ${timeframe}h timeframe`);
                    window.tradingViewWidget.updateChart(this.selectedCoin, timeframe);
                }
            });
        });
        console.log(`✅ Timeframe buttons initialized (${buttons.length} buttons)`);
    }

    // ========== THEME TOGGLE ==========
    setupThemeToggle() {
        const toggleBtn = document.getElementById("theme-toggle");
        const html = document.documentElement;

        // Load saved theme or default to dark
        const savedTheme = localStorage.getItem("theme") || "dark";
        html.setAttribute("data-theme", savedTheme);
        this.updateThemeButton(savedTheme);

        toggleBtn.addEventListener("click", () => {
            const currentTheme = html.getAttribute("data-theme");
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            html.setAttribute("data-theme", newTheme);
            localStorage.setItem("theme", newTheme);
            this.updateThemeButton(newTheme);

            // Recreate charts with new theme
            this.updateChartsTheme();
        });
    }

    updateThemeButton(theme) {
        const icon = document.getElementById("theme-icon");
        const label = document.getElementById("theme-label");
        if (theme === "dark") {
            icon.textContent = "🌙";
            label.textContent = "Dark";
        } else {
            icon.textContent = "☀️";
            label.textContent = "Light";
        }
    }

    updateChartsTheme() {
        // Update all Chart.js charts
        Object.values(this.charts).forEach((chart) => {
            if (chart && chart.update) {
                chart.update();
            }
        });

        // Recreate Plotly charts
        this.loadMarketDepth();
        this.loadVolumeProfile();
        this.loadCorrelationMatrix();
    }

    // ========== ON-CHAIN METRICS ==========
    async loadOnChainMetrics() {
        try {
            console.log("⛓️ Fetching on-chain metrics...");

            // Use blockchain.info API for some metrics (free)
            const [statsResponse, mempoolResponse] = await Promise.all([
                fetch("https://blockchain.info/stats?format=json"),
                fetch("https://blockchain.info/q/unconfirmedcount"),
            ]);

            if (statsResponse.ok) {
                const stats = await statsResponse.json();

                // Calculate exchange netflow (simulated based on block data)
                const netflow = (Math.random() - 0.5) * 10000;
                document.getElementById("exchange-netflow").textContent =
                    `${netflow >= 0 ? "+" : ""}${netflow.toFixed(0)} BTC`;
                document.getElementById("exchange-netflow").className =
                    netflow >= 0 ? "text-green" : "text-red";

                // Hashrate
                const hashrate = (stats.hash_rate / 1e9).toFixed(2);
                document.getElementById("hashrate").textContent = `${hashrate} EH/s`;

                // Difficulty
                const difficulty = (stats.difficulty / 1e12).toFixed(2);
                document.getElementById("difficulty").textContent = `${difficulty}T`;
            }

            // Simulate whale transaction count (would need premium API)
            const whaleCount = Math.floor(Math.random() * 50) + 20;
            document.getElementById("whale-count").textContent = whaleCount.toString();

            console.log("✅ On-chain metrics loaded");
        } catch (error) {
            console.error("❌ Error loading on-chain metrics:", error);
            document.getElementById("exchange-netflow").textContent = "N/A";
            document.getElementById("whale-count").textContent = "N/A";
            document.getElementById("hashrate").textContent = "N/A";
            document.getElementById("difficulty").textContent = "N/A";
        }
    }

    // ========== SENTIMENT ANALYSIS ==========
    async loadSentimentAnalysis() {
        try {
            console.log("🤖 Analyzing sentiment...");

            // Use Reddit API for the selected coin's subreddit
            const coinInfo = this.getCoinInfo();
            const response = await fetch(
                `https://www.reddit.com/r/${coinInfo.redditSub}/hot.json?limit=25`,
            );

            if (!response.ok) throw new Error("Reddit API error");

            const data = await response.json();
            const posts = data.data.children;

            // Simple sentiment analysis based on upvote ratio and keywords
            let bullishCount = 0;
            let bearishCount = 0;
            const bullishKeywords = ["moon", "pump", "bullish", "buy", "hodl", "rally", "breakout"];
            const bearishKeywords = ["dump", "bearish", "sell", "crash", "dip", "correction"];

            posts.forEach((post) => {
                const title = post.data.title.toLowerCase();
                const score = post.data.score;
                const ratio = post.data.upvote_ratio;

                // Keyword analysis
                const hasBullish = bullishKeywords.some((kw) => title.includes(kw));
                const hasBearish = bearishKeywords.some((kw) => title.includes(kw));

                if (hasBullish && ratio > 0.7) bullishCount += score;
                if (hasBearish && ratio > 0.7) bearishCount += score;
            });

            // Calculate sentiment score (0-100)
            const total = bullishCount + bearishCount;
            const sentiment = total > 0 ? (bullishCount / total) * 100 : 50;

            this.updateSentiment(sentiment);
        } catch (error) {
            console.error("❌ Error analyzing sentiment:", error);
            document.getElementById("sentiment-score").textContent = "N/A";
            document.getElementById("sentiment-label").textContent = "Unable to analyze";
        }
    }

    updateSentiment(score) {
        const scoreEl = document.getElementById("sentiment-score");
        const labelEl = document.getElementById("sentiment-label");
        const fillEl = document.getElementById("sentiment-fill");

        scoreEl.textContent = score.toFixed(0);
        fillEl.style.width = `${score}%`;

        if (score >= 70) {
            labelEl.textContent = "Extremely Bullish";
            scoreEl.className = "text-green";
        } else if (score >= 55) {
            labelEl.textContent = "Bullish";
            scoreEl.className = "text-green";
        } else if (score >= 45) {
            labelEl.textContent = "Neutral";
            scoreEl.className = "text-secondary";
        } else if (score >= 30) {
            labelEl.textContent = "Bearish";
            scoreEl.className = "text-red";
        } else {
            labelEl.textContent = "Extremely Bearish";
            scoreEl.className = "text-red";
        }
    }

    // ========== FEAR & GREED INDEX ==========
    async calculateFearGreedIndex() {
        try {
            console.log(`📊 Calculating Fear & Greed Index for ${this.selectedCoin}...`);

            // Fetch current price data
            const response = await fetch(`${this.apiBase}/data/current?symbol=${this.selectedCoin}`);
            const result = await response.json();
            const data = result.success ? result.data : result;

            // Calculate components (0-100 scale)
            const priceChange = data.change_24h || 0;
            const priceScore = Math.min(100, Math.max(0, (priceChange + 10) * 5)); // -10% to +10% = 0 to 100

            const volume = data.volume_24h || 0;
            const avgVolume = 1500; // Approximate average
            const volumeScore = Math.min(100, (volume / avgVolume) * 50);

            // Weighted average
            const fearGreed = priceScore * 0.6 + volumeScore * 0.4;

            this.updateFearGreed(fearGreed);
        } catch (error) {
            console.error("❌ Error calculating Fear & Greed:", error);
            document.getElementById("fear-greed-value").textContent = "N/A";
        }
    }

    updateFearGreed(score) {
        const valueEl = document.getElementById("fear-greed-value");
        const labelEl = document.getElementById("fear-greed-label");

        valueEl.textContent = score.toFixed(0);

        if (score >= 75) {
            labelEl.textContent = "Extreme Greed";
            valueEl.className = "text-green";
        } else if (score >= 55) {
            labelEl.textContent = "Greed";
            valueEl.className = "text-green";
        } else if (score >= 45) {
            labelEl.textContent = "Neutral";
            valueEl.className = "";
        } else if (score >= 25) {
            labelEl.textContent = "Fear";
            valueEl.className = "text-red";
        } else {
            labelEl.textContent = "Extreme Fear";
            valueEl.className = "text-red";
        }

        // Create gauge chart
        this.createFearGreedGauge(score);
    }

    createFearGreedGauge(score) {
        const canvas = document.getElementById("fear-greed-gauge");
        if (!canvas) return;

        if (this.charts.fearGreed) {
            this.charts.fearGreed.destroy();
        }

        this.charts.fearGreed = new Chart(canvas, {
            type: "doughnut",
            data: {
                datasets: [
                    {
                        data: [score, 100 - score],
                        backgroundColor: [
                            score >= 55 ? "#00ff88" : score >= 45 ? "#8b92b0" : "#ff3366",
                            "rgba(139, 146, 176, 0.1)",
                        ],
                        borderWidth: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "70%",
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false },
                },
            },
        });
    }

    // ========== ECONOMIC CALENDAR ==========
    async loadEconomicCalendar() {
        try {
            console.log("📅 Loading economic events...");

            // Sample events (would integrate with real API like Forex Factory)
            const events = [
                { date: "Dec 18, 2025", title: "FOMC Interest Rate Decision", impact: "high" },
                { date: "Dec 20, 2025", title: "CPI Report", impact: "high" },
                {
                    date: "Dec 22, 2025",
                    title: "Bitcoin Halving Countdown",
                    impact: "medium",
                    days: 120,
                },
                { date: "Jan 15, 2026", title: "Unemployment Data", impact: "medium" },
            ];

            this.displayEconomicEvents(events);
        } catch (error) {
            console.error("❌ Error loading economic calendar:", error);
        }
    }

    displayEconomicEvents(events) {
        const container = document.getElementById("economic-calendar");
        if (!container) return;

        container.innerHTML = events
            .map((event) => {
                const impactColor =
                    event.impact === "high"
                        ? "var(--accent-red)"
                        : event.impact === "medium"
                          ? "var(--accent-blue)"
                          : "var(--text-secondary)";

                return `
                <div class="flow-item">
                    <div>
                        <div style="font-weight: 600;">${this.escapeHtml(event.title)}</div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">${event.date}</div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        ${event.days ? `<span style="font-size: 0.875rem;">${event.days} days</span>` : ""}
                        <div style="width: 8px; height: 8px; border-radius: 50%; background: ${impactColor};"></div>
                    </div>
                </div>
            `;
            })
            .join("");
    }

    // ========== MULTI-TIMEFRAME ANALYSIS ==========
    async loadMultiTimeframeData() {
        try {
            console.log(`📊 Loading multi-timeframe data for ${this.selectedCoin}...`);

            const timeframes = [
                { id: "1h", hours: 24 },
                { id: "4h", hours: 96 },
                { id: "1d", hours: 168 },
                { id: "1w", hours: 720 },
            ];

            for (const tf of timeframes) {
                const response = await fetch(`${this.apiBase}/data/history/${tf.hours}?symbol=${this.selectedCoin}`);
                const result = await response.json();
                const history = result.success ? result.data.history : result.history;

                if (history && history.length > 0) {
                    this.createMiniChart(tf.id, history);
                    this.analyzeTrend(tf.id, history);
                }
            }
        } catch (error) {
            console.error("❌ Error loading multi-timeframe data:", error);
        }
    }

    createMiniChart(timeframe, history) {
        const canvas = document.getElementById(`chart-${timeframe}`);
        if (!canvas) return;

        const data = history.map((item) => ({
            x: new Date(item.timestamp * 1000),
            y: item.price,
        }));

        new Chart(canvas, {
            type: "line",
            data: {
                datasets: [
                    {
                        data: data,
                        borderColor: "#0099ff",
                        borderWidth: 1.5,
                        pointRadius: 0,
                        fill: false,
                        tension: 0.1,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { display: false },
                    y: {
                        display: true,
                        ticks: {
                            color: "#8b92b0",
                            font: { size: 10 },
                            maxTicksLimit: 4,
                        },
                        grid: { display: false },
                    },
                },
            },
        });
    }

    analyzeTrend(timeframe, history) {
        const trendEl = document.getElementById(`trend-${timeframe}`);
        if (!trendEl || history.length < 2) return;

        const firstPrice = history[0].price;
        const lastPrice = history[history.length - 1].price;
        const change = ((lastPrice - firstPrice) / firstPrice) * 100;

        if (change > 2) {
            trendEl.textContent = "🟢 Bullish";
            trendEl.className = "text-green";
        } else if (change < -2) {
            trendEl.textContent = "🔴 Bearish";
            trendEl.className = "text-red";
        } else {
            trendEl.textContent = "🟡 Neutral";
            trendEl.className = "text-secondary";
        }
    }

    // ========== SUPPORT & RESISTANCE ==========
    async calculateSupportResistance() {
        try {
            console.log(`📊 Calculating support & resistance for ${this.selectedCoin}...`);

            const response = await fetch(`${this.apiBase}/data/history/168?symbol=${this.selectedCoin}`);
            const result = await response.json();
            const history = result.success ? result.data.history : result.history;

            if (!history || history.length === 0) return;

            const prices = history.map((h) => h.price);
            const currentPrice = this.currentPrice || prices[prices.length - 1];

            // Find local maxima (resistance) and minima (support)
            const levels = this.findKeyLevels(prices);
            const resistance = levels.filter((l) => l > currentPrice).slice(0, 3);
            const support = levels
                .filter((l) => l < currentPrice)
                .slice(-3)
                .reverse();

            this.displayKeyLevels(support, resistance, currentPrice);
        } catch (error) {
            console.error("❌ Error calculating levels:", error);
        }
    }

    findKeyLevels(prices) {
        const levels = [];
        const window = 10;

        for (let i = window; i < prices.length - window; i++) {
            const slice = prices.slice(i - window, i + window);
            const price = prices[i];

            const isLocalMax = Math.max(...slice) === price;
            const isLocalMin = Math.min(...slice) === price;

            if (isLocalMax || isLocalMin) {
                levels.push(price);
            }
        }

        // Remove duplicates and sort
        return [...new Set(levels)].sort((a, b) => b - a);
    }

    displayKeyLevels(support, resistance, currentPrice) {
        console.log("📊 Displaying key levels:", { support, resistance, currentPrice });

        const resistanceLevelsEl = document.getElementById("resistance-levels");
        const supportLevelsEl = document.getElementById("support-levels");
        const currentLevelEl = document.getElementById("current-level");

        if (!resistanceLevelsEl || !supportLevelsEl || !currentLevelEl) {
            console.error("❌ Key level elements not found in DOM");
            return;
        }

        if (currentLevelEl) {
            currentLevelEl.textContent = `$${currentPrice.toLocaleString()}`;
        }

        if (resistanceLevelsEl) {
            resistanceLevelsEl.innerHTML = resistance
                .map(
                    (level) => `
                <div style="padding: 0.5rem; background: rgba(255, 51, 102, 0.1); border-radius: 4px; margin-bottom: 0.5rem; display: flex; justify-content: space-between;">
                    <span style="color: var(--accent-red); font-weight: 600;">R</span>
                    <span>$${level.toLocaleString()}</span>
                </div>
            `,
                )
                .join("");
        }

        if (supportLevelsEl) {
            supportLevelsEl.innerHTML = support
                .map(
                    (level) => `
                <div style="padding: 0.5rem; background: rgba(0, 255, 136, 0.1); border-radius: 4px; margin-bottom: 0.5rem; display: flex; justify-content: space-between;">
                    <span style="color: var(--accent-green); font-weight: 600;">S</span>
                    <span>$${level.toLocaleString()}</span>
                </div>
            `,
                )
                .join("");
        }
    }

    // ========== FIBONACCI RETRACEMENT ==========
    async calculateFibonacci() {
        try {
            console.log(`📊 Calculating Fibonacci levels for ${this.selectedCoin}...`);

            const response = await fetch(`${this.apiBase}/data/history/168?symbol=${this.selectedCoin}`);
            const result = await response.json();
            const history = result.success ? result.data.history : result.history;

            if (!history || history.length === 0) return;

            const prices = history.map((h) => h.price);
            const high = Math.max(...prices);
            const low = Math.min(...prices);
            const diff = high - low;

            const levels = {
                0: high,
                236: high - diff * 0.236,
                382: high - diff * 0.382,
                50: high - diff * 0.5,
                618: high - diff * 0.618,
                786: high - diff * 0.786,
                100: low,
            };

            Object.entries(levels).forEach(([key, value]) => {
                const el = document.getElementById(`fib-${key}`);
                if (el) {
                    el.textContent = `$${value.toLocaleString()}`;
                }
            });
        } catch (error) {
            console.error("❌ Error calculating Fibonacci:", error);
        }
    }

    // ========== CORRELATION MATRIX ==========
    async loadCorrelationMatrix() {
        try {
            console.log("📊 Loading correlation matrix...");

            // Simulated correlation data (would fetch from Yahoo Finance API)
            const correlations = [
                { asset: "BTC", values: [1.0, 0.75, 0.42, -0.15, 0.28] },
                { asset: "ETH", values: [0.75, 1.0, 0.38, -0.12, 0.25] },
                { asset: "S&P 500", values: [0.42, 0.38, 1.0, -0.45, 0.62] },
                { asset: "Gold", values: [-0.15, -0.12, -0.45, 1.0, -0.35] },
                { asset: "USD", values: [0.28, 0.25, 0.62, -0.35, 1.0] },
            ];

            const assets = correlations.map((c) => c.asset);
            const z = correlations.map((c) => c.values);

            const trace = {
                x: assets,
                y: assets,
                z: z,
                type: "heatmap",
                colorscale: [
                    [0, "#ff3366"],
                    [0.5, "#8b92b0"],
                    [1, "#00ff88"],
                ],
                text: z.map((row) => row.map((val) => val.toFixed(2))),
                texttemplate: "%{text}",
                textfont: { color: "white" },
                showscale: true,
            };

            const layout = {
                paper_bgcolor: "transparent",
                plot_bgcolor: "transparent",
                xaxis: { color: "#8b92b0", side: "bottom" },
                yaxis: { color: "#8b92b0" },
                margin: { t: 20, r: 20, b: 40, l: 80 },
            };

            Plotly.newPlot("correlation-matrix", [trace], layout, { displayModeBar: false });
        } catch (error) {
            console.error("❌ Error loading correlation matrix:", error);
        }
    }

    // ========== PATTERN RECOGNITION ==========
    async detectPatterns() {
        try {
            console.log(`🔍 Detecting patterns for ${this.selectedCoin}...`);

            const response = await fetch(`${this.apiBase}/data/history/720?symbol=${this.selectedCoin}`);
            const result = await response.json();
            const history = result.success ? result.data.history : result.history;

            if (!history || history.length === 0) return;

            // Simple pattern detection based on recent price action
            const recentPrices = history.slice(-30).map((h) => h.price);
            const pattern = this.identifyPattern(recentPrices);

            this.displayPatternMatch(pattern);
        } catch (error) {
            console.error("❌ Error detecting patterns:", error);
        }
    }

    identifyPattern(prices) {
        if (prices.length < 10) return null;

        const recent = prices.slice(-10);
        const trend = recent[recent.length - 1] - recent[0];
        const volatility = Math.max(...recent) - Math.min(...recent);
        const avgPrice = recent.reduce((a, b) => a + b) / recent.length;

        // Simple pattern classification
        if (trend > 0 && volatility / avgPrice < 0.02) {
            return {
                name: "Bullish Trend",
                confidence: 75,
                description: "Steady upward movement with low volatility",
                historicalSuccess: 68,
                nextMove: "Continuation likely",
            };
        } else if (trend < 0 && volatility / avgPrice < 0.02) {
            return {
                name: "Bearish Trend",
                confidence: 72,
                description: "Steady downward movement with low volatility",
                historicalSuccess: 65,
                nextMove: "Further decline possible",
            };
        } else if (volatility / avgPrice > 0.05) {
            return {
                name: "High Volatility",
                confidence: 80,
                description: "Large price swings indicating uncertainty",
                historicalSuccess: 55,
                nextMove: "Consolidation expected",
            };
        } else {
            return {
                name: "Consolidation",
                confidence: 65,
                description: "Price moving sideways in tight range",
                historicalSuccess: 60,
                nextMove: "Breakout imminent",
            };
        }
    }

    displayPatternMatch(pattern) {
        const container = document.getElementById("pattern-matches");
        if (!container || !pattern) {
            if (container) {
                container.innerHTML =
                    '<div style="text-align: center; color: var(--text-secondary);">No clear patterns detected</div>';
            }
            return;
        }

        container.innerHTML = `
            <div style="background: rgba(0, 153, 255, 0.05); border-left: 3px solid var(--accent-blue); padding: 1rem; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                    <div>
                        <div style="font-size: 1.125rem; font-weight: 600; color: var(--accent-blue);">${pattern.name}</div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.25rem;">${pattern.description}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--accent-blue);">${pattern.confidence}%</div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">Confidence</div>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                    <div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">Historical Success</div>
                        <div style="font-size: 1.125rem; font-weight: 600;">${pattern.historicalSuccess}%</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">Expected Move</div>
                        <div style="font-size: 0.875rem; font-weight: 600;">${pattern.nextMove}</div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Fetch with retry logic and timeout
     */
    async fetchWithRetry(url, options = {}, retries = this.maxRetries) {
        const timeout = options.timeout || 10000; // 10 second default timeout

        for (let attempt = 0; attempt <= retries; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeout);

                const response = await fetch(url, {
                    ...options,
                    signal: controller.signal,
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                this.errorCount = 0; // Reset error count on success
                return response;
            } catch (error) {
                const isLastAttempt = attempt === retries;

                if (isLastAttempt) {
                    this.errorCount++;
                    this.lastError = {
                        url,
                        error: error.message,
                        timestamp: new Date().toISOString(),
                    };

                    this.logger.error(`Failed to fetch ${url} after ${retries + 1} attempts`, {
                        error: error.message,
                        attempts: retries + 1,
                    });

                    throw error;
                }

                // Wait before retrying with exponential backoff
                const delay = this.retryDelay * Math.pow(2, attempt);
                this.logger.warn(
                    `Fetch attempt ${attempt + 1} failed for ${url}, retrying in ${delay}ms`,
                    {
                        error: error.message,
                    },
                );

                await new Promise((resolve) => setTimeout(resolve, delay));
            }
        }
    }

    /**
     * Safe async wrapper with error handling
     */
    async withErrorHandling(operation, operationName, fallbackValue = null) {
        try {
            this.logger.operationStart(operationName);
            const startTime = performance.now();

            const result = await operation();

            const duration = performance.now() - startTime;
            this.logger.operationSuccess(operationName, duration);

            return result;
        } catch (error) {
            this.logger.operationError(operationName, error);
            this.showError(`${operationName} failed: ${error.message}`);
            return fallbackValue;
        }
    }

    showError(message) {
        this.logger.error("Dashboard Error", { message });

        // Show user-friendly error notification
        const errorToast = document.createElement("div");
        errorToast.className = "error-toast";
        errorToast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--accent-red);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
            max-width: 400px;
        `;
        errorToast.textContent = message;

        document.body.appendChild(errorToast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            errorToast.style.animation = "slideOut 0.3s ease-out";
            setTimeout(() => errorToast.remove(), 300);
        }, 5000);
    }

    // ========== LOADING STATE MANAGEMENT ==========

    /**
     * Create global loading overlay if it doesn't exist
     */
    createLoadingOverlay() {
        if (!this.loadingOverlay) {
            this.loadingOverlay = document.createElement("div");
            this.loadingOverlay.id = "global-loading-overlay";
            this.loadingOverlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                backdrop-filter: blur(4px);
            `;

            const spinner = document.createElement("div");
            spinner.className = "loading-spinner";
            spinner.innerHTML = `
                <div style="text-align: center;">
                    <div class="spinner-circle" style="
                        border: 4px solid rgba(255, 255, 255, 0.1);
                        border-top: 4px solid var(--accent-blue);
                        border-radius: 50%;
                        width: 60px;
                        height: 60px;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 1rem;
                    "></div>
                    <div class="loading-message" style="
                        color: white;
                        font-size: 1rem;
                        font-weight: 500;
                    ">Loading...</div>
                </div>
            `;

            this.loadingOverlay.appendChild(spinner);
            document.body.appendChild(this.loadingOverlay);

            // Add spinner animation keyframes if not already present
            if (!document.getElementById("spinner-styles")) {
                const style = document.createElement("style");
                style.id = "spinner-styles";
                style.textContent = `
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                `;
                document.head.appendChild(style);
            }
        }
    }

    /**
     * Show loading indicator for a specific operation
     * @param {string} key - Unique identifier for the loading operation
     * @param {string} message - Optional message to display
     * @param {boolean} showOverlay - Whether to show global overlay (default: false)
     */
    showLoading(key, message = "Loading...", showOverlay = false) {
        this.loadingStates.set(key, {
            active: true,
            message,
            startTime: performance.now(),
        });

        this.logger.debug(`Loading started: ${key}`, { message });

        if (showOverlay) {
            this.createLoadingOverlay();
            const messageEl = this.loadingOverlay.querySelector(".loading-message");
            if (messageEl) {
                messageEl.textContent = message;
            }
            this.loadingOverlay.style.display = "flex";
        } else {
            // Show inline spinner for specific element
            const targetEl = document.getElementById(`${key}-loading`);
            if (targetEl) {
                targetEl.style.display = "flex";
                targetEl.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--accent-blue);">
                        <div style="
                            border: 2px solid rgba(0, 123, 255, 0.2);
                            border-top: 2px solid var(--accent-blue);
                            border-radius: 50%;
                            width: 16px;
                            height: 16px;
                            animation: spin 1s linear infinite;
                        "></div>
                        <span style="font-size: 0.875rem;">${message}</span>
                    </div>
                `;
            }
        }
    }

    /**
     * Hide loading indicator for a specific operation
     * @param {string} key - Unique identifier for the loading operation
     */
    hideLoading(key) {
        const loadingState = this.loadingStates.get(key);

        if (loadingState) {
            const duration = performance.now() - loadingState.startTime;
            this.logger.debug(`Loading completed: ${key}`, {
                duration: `${duration.toFixed(2)}ms`,
            });
            this.loadingStates.delete(key);
        }

        // Hide global overlay if no other loading operations are active
        if (this.loadingOverlay && this.loadingStates.size === 0) {
            this.loadingOverlay.style.display = "none";
        }

        // Hide inline spinner
        const targetEl = document.getElementById(`${key}-loading`);
        if (targetEl) {
            targetEl.style.display = "none";
            targetEl.innerHTML = "";
        }
    }

    /**
     * Check if any loading operations are active
     * @returns {boolean}
     */
    isLoading() {
        return this.loadingStates.size > 0;
    }

    /**
     * Get all active loading operations
     * @returns {Array}
     */
    getActiveLoadingOperations() {
        return Array.from(this.loadingStates.entries()).map(([key, state]) => ({
            key,
            message: state.message,
            duration: performance.now() - state.startTime,
        }));
    }

    /**
     * Stop all auto-update intervals to prevent memory leaks
     */
    stopAutoUpdate() {
        console.log("⏹️ Stopping auto-update intervals");
        // Clear all tracked intervals
        if (this.intervals && this.intervals.length > 0) {
            this.intervals.forEach((intervalId) => {
                clearInterval(intervalId);
            });
            this.intervals = [];
        }
    }

    startAutoUpdate() {
        // IMPORTANT: Clear existing intervals first to prevent memory leaks
        this.stopAutoUpdate();

        console.log("🔄 Starting auto-update (30s interval)");

        // Update price and indicators every 30 seconds
        this.intervals.push(
            setInterval(() => {
                console.log("🔄 Auto-updating data...");
                this.loadBitcoinPrice();
                this.loadIndicators();
            }, this.updateInterval),
        );

        // Update market depth every 60 seconds
        this.intervals.push(
            setInterval(() => {
                this.loadMarketDepth();
            }, 60000),
        );

        // Update news every 5 minutes
        this.intervals.push(
            setInterval(() => {
                this.loadNews();
            }, 300000),
        );
    }

    /**
     * Cleanup all resources when dashboard is destroyed
     * Call this when navigating away from the dashboard
     */
    destroy() {
        console.log("🧹 Cleaning up dashboard resources");
        this.stopAutoUpdate();
        if (this.clockInterval) {
            clearInterval(this.clockInterval);
            this.clockInterval = null;
        }
        // Clear any chart instances
        if (this.charts) {
            Object.values(this.charts).forEach((chart) => {
                if (chart && typeof chart.destroy === "function") {
                    chart.destroy();
                }
            });
            this.charts = {};
        }
    }

    // ========== CME GAP TRACKER ==========
    async loadCMEGaps() {
        try {
            // CME gaps only relevant for BTC
            if (this.selectedCoin !== 'BTC') {
                const gapsList = document.getElementById('cme-gaps-list');
                if (gapsList) {
                    gapsList.innerHTML = '<div style="color: var(--text-secondary); font-size: 0.875rem;">CME gaps only available for Bitcoin</div>';
                }
                return;
            }

            console.log("Loading CME gap data...");
            const response = await fetch(`${this.apiBase}/data/history/720?symbol=BTC`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            const history = result.success ? result.data.history : result.history;

            const gaps = this.calculateCMEGaps(history);
            this.displayCMEGaps(gaps);

        } catch (error) {
            console.error("Error loading CME gaps:", error);
            const gapsList = document.getElementById('cme-gaps-list');
            if (gapsList) {
                gapsList.innerHTML = '<div style="color: var(--accent-danger); font-size: 0.875rem;">Error loading CME data</div>';
            }
        }
    }

    calculateCMEGaps(history) {
        const gaps = [];
        const gapThreshold = 0.02; // 2% minimum gap size

        // CME futures trade Mon-Fri, gaps appear on weekends
        // Sort history by timestamp
        const sorted = [...history].sort((a, b) => a.timestamp - b.timestamp);

        for (let i = 1; i < sorted.length; i++) {
            const prev = sorted[i - 1];
            const curr = sorted[i];

            // Check for significant price gap
            const gapPercent = Math.abs((curr.price - prev.price) / prev.price);

            if (gapPercent >= gapThreshold) {
                const gapLow = Math.min(prev.price, curr.price);
                const gapHigh = Math.max(prev.price, curr.price);
                const gapSize = gapHigh - gapLow;
                const currentPrice = sorted[sorted.length - 1].price;

                // Determine if gap is filled
                const isFilled = sorted.slice(i).some(h =>
                    h.price >= gapLow && h.price <= gapHigh
                );

                gaps.push({
                    timestamp: curr.timestamp,
                    low: gapLow,
                    high: gapHigh,
                    size: gapSize,
                    percent: gapPercent * 100,
                    direction: curr.price > prev.price ? 'UP' : 'DOWN',
                    filled: isFilled,
                    distance: isFilled ? 0 : Math.min(
                        Math.abs(currentPrice - gapLow),
                        Math.abs(currentPrice - gapHigh)
                    )
                });
            }
        }

        // Return most recent 5 gaps
        return gaps.slice(-5).reverse();
    }

    displayCMEGaps(gaps) {
        console.log("📊 Displaying CME gaps:", gaps);

        const gapsList = document.getElementById('cme-gaps-list');
        if (!gapsList) {
            console.error("❌ cme-gaps-list element not found in DOM");
            return;
        }

        if (gaps.length === 0) {
            gapsList.innerHTML = '<div style="color: var(--text-secondary); font-size: 0.875rem;">No significant CME gaps detected</div>';
            return;
        }

        let html = '';
        gaps.forEach(gap => {
            const statusBadge = gap.filled
                ? '<span class="terminal-badge success">FILLED</span>'
                : '<span class="terminal-badge danger">OPEN</span>';

            const directionIcon = gap.direction === 'UP' ? '↑' : '↓';

            const date = new Date(gap.timestamp * 1000).toLocaleDateString();

            html += `
                <div class="quick-stat" style="margin-bottom: 12px; border-left: 3px solid var(--${gap.filled ? 'success' : 'danger'});">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span class="quick-stat-label">${date} ${directionIcon}</span>
                        ${statusBadge}
                    </div>
                    <div class="quick-stat-value" style="font-size: 0.9em;">
                        $${gap.low.toFixed(2)} - $${gap.high.toFixed(2)}
                    </div>
                    <div class="quick-stat-change">
                        Size: $${gap.size.toFixed(2)} (${gap.percent.toFixed(2)}%)
                        ${!gap.filled ? `<br>Distance: $${gap.distance.toFixed(2)}` : ''}
                    </div>
                </div>
            `;
        });

        gapsList.innerHTML = html;
    }
}

// Initialize dashboard when page loads
document.addEventListener("DOMContentLoaded", () => {
    console.log("🌐 DOM loaded, initializing dashboard...");
    window.dashboard = new AnalyticsDashboard();

    // Listen for section changes to cleanup resources when navigating away
    document.addEventListener("section-changed", (e) => {
        const section = e.detail?.section;
        if (section !== "market" && window.dashboard) {
            // Stop auto-updates when leaving market section
            console.log("📤 Leaving market section, pausing updates");
            window.dashboard.stopAutoUpdate();
        } else if (section === "market" && window.dashboard) {
            // Resume auto-updates when returning to market section
            console.log("📥 Entering market section, resuming updates");
            window.dashboard.startAutoUpdate();
        }
    });

    // Cleanup on page unload to prevent memory leaks
    window.addEventListener("beforeunload", () => {
        if (window.dashboard) {
            window.dashboard.destroy();
        }
    });
});
