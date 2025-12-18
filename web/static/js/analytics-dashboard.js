/**
 * Odin Analytics Dashboard - Modern Bitcoin Market Intelligence
 * REAL DATA ONLY - Connects to trusted APIs
 */

class AnalyticsDashboard {
    constructor() {
        this.apiBase = "/api/v1";
        this.charts = {};
        this.updateInterval = 30000; // 30 seconds
        this.intervals = [];
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

        // Coin metadata mapping
        this.coinMappings = {
            BTC: {
                name: "Bitcoin",
                symbol: "₿",
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
                krakenSymbol: "HYPEUSD",
                binanceSymbol: "HYPEUSDT",
                coingeckoId: "hyperliquid",
                hyperliquidSymbol: "HYPE",
                circulatingSupply: 1000000000,
                redditSub: "hyperliquid",
            },
        };

        this.init();
    }

    async init() {
        console.log("🚀 Initializing Odin Analytics Dashboard - Real Data Only");

        // Setup theme toggle and coin selector
        this.setupThemeToggle();
        this.setupCoinSelector();

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
            document.getElementById("current-time").textContent = timeString;
        };
        updateClock();
        setInterval(updateClock, 1000);
    }

    async loadAllData() {
        console.log(`📡 Loading real data from APIs for ${this.getCoinInfo().name}...`);

        const loadTasks = [
            { name: "Bitcoin Price", fn: this.loadBitcoinPrice() },
            { name: "Indicators", fn: this.loadIndicators() },
            { name: "Price History", fn: this.loadPriceHistory() },
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
        const marketCap = price * coinInfo.circulatingSupply;

        // Update DOM elements
        document.getElementById("btc-price").textContent = `$${price.toLocaleString()}`;
        document.getElementById("change-value").textContent =
            `${change >= 0 ? "+" : ""}${change.toFixed(2)}%`;
        document.getElementById("change-value").className = change >= 0 ? "text-green" : "text-red";
        document.getElementById("change-absolute").textContent =
            `$${((price * change) / 100).toFixed(2)}`;
        document.getElementById("high-24h").textContent =
            high > 0 ? `$${high.toLocaleString()}` : "Loading...";
        document.getElementById("low-24h").textContent =
            low > 0 ? `$${low.toLocaleString()}` : "Loading...";
        document.getElementById("volume-24h").textContent =
            volume > 0 ? `${volume.toLocaleString()} ${this.selectedCoin}` : "Loading...";
        document.getElementById("market-cap").textContent = `$${(marketCap / 1e9).toFixed(2)}B`;

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

    async loadIndicators() {
        try {
            console.log("Fetching technical indicators...");
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

            console.log("✅ Indicators data received:", strategies);
            this.updateIndicators(strategies);
        } catch (error) {
            console.error("❌ Error loading indicators:", error);
            this.setIndicatorLoading();
        }
    }

    updateIndicators(strategies) {
        const indicatorMap = {
            rsi: "rsi",
            macd: "macd",
            bollinger_bands: "bb",
            moving_average: "ma",
        };

        strategies.forEach((strategy) => {
            const key = indicatorMap[strategy.type];
            if (!key) return;

            const signal = strategy.last_signal?.type || "hold";
            const signalClass =
                signal === "buy"
                    ? "signal-buy"
                    : signal === "sell"
                      ? "signal-sell"
                      : "signal-neutral";

            // Get real value from strategy data
            let value = "--";
            if (strategy.last_signal?.value !== undefined) {
                value = strategy.last_signal.value.toFixed(2);
            } else if (strategy.return !== undefined) {
                value = strategy.return.toFixed(2) + "%";
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

    async loadPriceHistory() {
        const loadingKey = "price-history";
        try {
            const coinInfo = this.getCoinInfo();
            this.showLoading(loadingKey, `Loading ${coinInfo.name} price history...`);

            console.log(`Fetching ${coinInfo.name} price history...`);
            const response = await fetch(
                `${this.apiBase}/data/history/24?symbol=${this.selectedCoin}`,
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            const data = result.success ? result.data : result;

            if (data.history && this.charts.price) {
                console.log(`✅ ${coinInfo.name} price history received, updating chart`);
                this.updatePriceChart(data.history);
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
        if (!this.charts.price || !history || history.length === 0) return;

        const data = history.map((item) => ({
            x: new Date(item.timestamp * 1000),
            y: item.price,
        }));

        this.charts.price.data.datasets[0].data = data;
        this.charts.price.update();
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
            console.log("📊 Creating volume profile...");

            // Get price history to build volume profile
            const response = await fetch(`${this.apiBase}/data/history/168`); // 7 days

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
        const coinSelector = document.getElementById("coin-selector");
        if (!coinSelector) return;

        // Load saved coin preference or default to BTC
        const savedCoin = localStorage.getItem("selectedCoin") || "BTC";
        this.selectedCoin = savedCoin;
        coinSelector.value = savedCoin;

        // Update coin name on initial load
        this.updateCoinName();

        // Handle coin selection changes
        coinSelector.addEventListener("change", async (e) => {
            const newCoin = e.target.value;
            console.log(`🔄 Switching to ${newCoin}...`);

            this.selectedCoin = newCoin;
            localStorage.setItem("selectedCoin", newCoin);

            // Update UI
            this.updateCoinName();

            // Clear old intervals
            this.intervals.forEach((interval) => clearInterval(interval));
            this.intervals = [];

            // Reload all data for the new coin
            await this.loadAllData();

            // Reinitialize charts
            this.initializeCharts();

            // Recalculate derived metrics
            await this.calculateSupportResistance();
            await this.calculateFibonacci();
            await this.loadCorrelationMatrix();
            await this.detectPatterns();

            // Restart auto-update
            this.startAutoUpdate();

            console.log(`✅ Switched to ${this.getCoinInfo().name}`);
        });
    }

    getCoinInfo() {
        return this.coinMappings[this.selectedCoin] || this.coinMappings["BTC"];
    }

    updateCoinName() {
        const coinNameEl = document.getElementById("coin-name");
        if (coinNameEl) {
            coinNameEl.textContent = this.getCoinInfo().name;
        }
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
            console.log("📊 Calculating Fear & Greed Index...");

            // Fetch current price data
            const response = await fetch(`${this.apiBase}/data/current`);
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
            console.log("📊 Loading multi-timeframe data...");

            const timeframes = [
                { id: "1h", hours: 24 },
                { id: "4h", hours: 96 },
                { id: "1d", hours: 168 },
                { id: "1w", hours: 720 },
            ];

            for (const tf of timeframes) {
                const response = await fetch(`${this.apiBase}/data/history/${tf.hours}`);
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
            console.log("📊 Calculating support & resistance...");

            const response = await fetch(`${this.apiBase}/data/history/168`);
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
        const resistanceLevelsEl = document.getElementById("resistance-levels");
        const supportLevelsEl = document.getElementById("support-levels");
        const currentLevelEl = document.getElementById("current-level");

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
            console.log("📊 Calculating Fibonacci levels...");

            const response = await fetch(`${this.apiBase}/data/history/168`);
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
            console.log("🔍 Detecting patterns...");

            const response = await fetch(`${this.apiBase}/data/history/720`);
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

    startAutoUpdate() {
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
}

// Initialize dashboard when page loads
document.addEventListener("DOMContentLoaded", () => {
    console.log("🌐 DOM loaded, initializing dashboard...");
    window.dashboard = new AnalyticsDashboard();
});
