/**
 * Live Ticker Bar - Bloomberg-style multi-asset price ticker
 * Displays real-time prices for cryptocurrencies, precious metals, and stocks
 */

class LiveTickerBar {
    constructor(assets = null) {
        // Default assets: top cryptos, key metals, major stocks
        this.defaultAssets = [
            // Cryptocurrencies
            'BTC', 'ETH', 'SOL', 'XRP', 'BNB',
            // Precious Metals
            'GOLD', 'SILVER',
            // Major Stocks
            'SPY', 'NVDA', 'TSLA'
        ];
        this.assets = assets || this.defaultAssets;
        this.prices = {};
        this.updateInterval = 5000; // 5 seconds
        this.intervalId = null;
        this.apiBase = '/api/v1';

        // Asset display info with categories
        this.assetInfo = {
            // Cryptocurrencies
            'BTC': { name: 'Bitcoin', symbol: '₿', color: '#f7931a', category: 'crypto' },
            'ETH': { name: 'Ethereum', symbol: 'Ξ', color: '#627eea', category: 'crypto' },
            'SOL': { name: 'Solana', symbol: '◎', color: '#00d4aa', category: 'crypto' },
            'XRP': { name: 'XRP', symbol: '✕', color: '#23292f', category: 'crypto' },
            'BNB': { name: 'BNB', symbol: '◆', color: '#f3ba2f', category: 'crypto' },
            'SUI': { name: 'Sui', symbol: '〜', color: '#4da2ff', category: 'crypto' },
            'HYPE': { name: 'Hyperliquid', symbol: '⚡', color: '#00d4ff', category: 'crypto' },

            // Precious Metals
            'GOLD': { name: 'Gold', symbol: 'Au', color: '#ffd700', category: 'metal', unit: 'oz' },
            'SILVER': { name: 'Silver', symbol: 'Ag', color: '#c0c0c0', category: 'metal', unit: 'oz' },
            'PLATINUM': { name: 'Platinum', symbol: 'Pt', color: '#e5e4e2', category: 'metal', unit: 'oz' },
            'PALLADIUM': { name: 'Palladium', symbol: 'Pd', color: '#cec8c8', category: 'metal', unit: 'oz' },
            'COPPER': { name: 'Copper', symbol: 'Cu', color: '#b87333', category: 'metal', unit: 'lb' },

            // Stocks - Index ETFs
            'SPY': { name: 'S&P 500', symbol: '📈', color: '#1a73e8', category: 'stock', sector: 'Index' },
            'QQQ': { name: 'Nasdaq 100', symbol: '📊', color: '#00c853', category: 'stock', sector: 'Index' },

            // Stocks - Tech
            'AAPL': { name: 'Apple', symbol: '🍎', color: '#555555', category: 'stock', sector: 'Tech' },
            'MSFT': { name: 'Microsoft', symbol: 'MS', color: '#00a4ef', category: 'stock', sector: 'Tech' },
            'GOOGL': { name: 'Google', symbol: 'G', color: '#4285f4', category: 'stock', sector: 'Tech' },
            'AMZN': { name: 'Amazon', symbol: 'AZ', color: '#ff9900', category: 'stock', sector: 'Tech' },
            'NVDA': { name: 'NVIDIA', symbol: 'NV', color: '#76b900', category: 'stock', sector: 'Tech' },
            'TSLA': { name: 'Tesla', symbol: 'TS', color: '#cc0000', category: 'stock', sector: 'Tech' },
            'META': { name: 'Meta', symbol: 'MT', color: '#0668e1', category: 'stock', sector: 'Tech' },

            // Stocks - Crypto-related
            'COIN': { name: 'Coinbase', symbol: 'CB', color: '#0052ff', category: 'stock', sector: 'Crypto' },
            'MSTR': { name: 'MicroStrategy', symbol: 'MR', color: '#d9232d', category: 'stock', sector: 'Crypto' }
        };

        // Backwards compatibility alias
        this.coinInfo = this.assetInfo;
        this.coins = this.assets;
    }

    /**
     * Initialize the ticker bar
     */
    async init() {
        console.log('🎯 Initializing Live Ticker Bar...');

        // Initial render with placeholder data
        this.render();

        // Fetch initial prices
        await this.fetchAllPrices();

        // Start auto-update
        this.start();

        // Add click handlers
        this.attachClickHandlers();

        console.log('✅ Live Ticker Bar initialized');
    }

    /**
     * Fetch prices for all assets in parallel
     */
    async fetchAllPrices() {
        try {
            const promises = this.assets.map(asset =>
                fetch(`${this.apiBase}/data/price?symbol=${asset}`)
                    .then(res => res.json())
                    .then(result => {
                        // Handle API response format
                        const data = result.success && result.data ? result.data : result;
                        return { asset, data };
                    })
                    .catch(err => {
                        console.warn(`⚠️ Failed to fetch ${asset} price:`, err);
                        return { asset, data: null };
                    })
            );

            const results = await Promise.all(promises);

            // Update prices object
            results.forEach(({ asset, data }) => {
                if (data && data.price) {
                    // Calculate change_percent if not provided
                    let change_percent = data.change_percent || data.change_24h || 0;

                    this.prices[asset] = {
                        price: data.price,
                        change_24h: data.change_24h || data.change_24h_abs || 0,
                        change_percent: change_percent,
                        volume_24h: data.volume_24h || data.volume || 0,
                        timestamp: Date.now()
                    };
                }
            });

            // Update the ticker display
            this.updateDisplay();
        } catch (error) {
            console.error('❌ Error fetching ticker prices:', error);
        }
    }

    /**
     * Get category badge class for styling
     */
    getCategoryBadge(category) {
        const badges = {
            'crypto': 'badge-crypto',
            'metal': 'badge-metal',
            'stock': 'badge-stock'
        };
        return badges[category] || 'badge-crypto';
    }

    /**
     * Render the ticker bar HTML
     */
    render() {
        const tickerContainer = document.getElementById('ticker-bar');
        if (!tickerContainer) {
            console.warn('⚠️ Ticker bar container not found');
            return;
        }

        let html = '';

        this.assets.forEach(asset => {
            const info = this.assetInfo[asset];
            if (!info) {
                console.warn(`⚠️ No info found for asset: ${asset}`);
                return;
            }

            const categoryClass = this.getCategoryBadge(info.category);
            const unitSuffix = info.unit ? `/${info.unit}` : '';

            html += `
                <div class="ticker-item ${categoryClass}" data-coin="${asset}" data-category="${info.category}">
                    <span class="ticker-symbol" style="color: ${info.color}">${info.symbol} ${asset}</span>
                    <span class="ticker-price" id="ticker-price-${asset}">$---.--${unitSuffix}</span>
                    <span class="ticker-change" id="ticker-change-${asset}">
                        <span class="ticker-change-icon">-</span>
                        <span class="ticker-change-value">-.--</span>%
                    </span>
                </div>
            `;
        });

        tickerContainer.innerHTML = html;
    }

    /**
     * Update the ticker display with latest prices
     */
    updateDisplay() {
        this.assets.forEach(asset => {
            const priceData = this.prices[asset];
            const info = this.assetInfo[asset];
            if (!priceData || !info) return;

            // Update price
            const priceEl = document.getElementById(`ticker-price-${asset}`);
            if (priceEl) {
                const formattedPrice = this.formatPrice(priceData.price, info.category);
                const unitSuffix = info.unit ? `/${info.unit}` : '';
                priceEl.textContent = `$${formattedPrice}${unitSuffix}`;

                // Add flash animation on price change
                priceEl.classList.add('ticker-flash');
                setTimeout(() => priceEl.classList.remove('ticker-flash'), 500);
            }

            // Update change
            const changeEl = document.getElementById(`ticker-change-${asset}`);
            if (changeEl) {
                const changePercent = priceData.change_percent || 0;
                const isPositive = changePercent >= 0;

                changeEl.className = 'ticker-change ' + (isPositive ? 'positive' : 'negative');

                const icon = changeEl.querySelector('.ticker-change-icon');
                const value = changeEl.querySelector('.ticker-change-value');

                if (icon) icon.textContent = isPositive ? '▲' : '▼';
                if (value) value.textContent = Math.abs(changePercent).toFixed(2);
            }
        });
    }

    /**
     * Format price based on value and asset category
     */
    formatPrice(price, category = 'crypto') {
        // Stocks and metals typically use 2 decimal places
        if (category === 'stock' || category === 'metal') {
            return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        // Crypto formatting based on price magnitude
        if (price >= 1000) {
            return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        } else if (price >= 1) {
            return price.toFixed(2);
        } else if (price >= 0.01) {
            return price.toFixed(4);
        } else {
            return price.toFixed(6);
        }
    }

    /**
     * Attach click handlers to ticker items using event delegation
     */
    attachClickHandlers() {
        const tickerContainer = document.getElementById('ticker-bar');
        if (!tickerContainer) {
            console.warn('⚠️ Cannot attach click handlers - ticker bar not found');
            return;
        }

        // Use event delegation for better reliability
        tickerContainer.addEventListener('click', (e) => {
            // Find the clicked ticker item
            const tickerItem = e.target.closest('.ticker-item');
            if (!tickerItem) return;

            const coin = tickerItem.dataset.coin;
            if (!coin) return;

            console.log(`🎯 Ticker clicked: ${coin}`);

            // Dispatch custom event for analytics dashboard to handle
            // The dashboard will update the dropdown after processing
            const event = new CustomEvent('ticker-coin-selected', {
                detail: { coin },
                bubbles: true
            });
            document.dispatchEvent(event);
            console.log(`📡 Dispatched ticker-coin-selected event for ${coin}`);
        });

        console.log('✅ Ticker click handlers attached (event delegation)');
    }

    /**
     * Start auto-update
     */
    start() {
        if (this.intervalId) {
            this.stop();
        }

        this.intervalId = setInterval(() => {
            this.fetchAllPrices();
        }, this.updateInterval);

        console.log(`🔄 Ticker auto-update started (${this.updateInterval / 1000}s interval)`);
    }

    /**
     * Stop auto-update
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            console.log('⏹️ Ticker auto-update stopped');
        }
    }

    /**
     * Get current price for an asset
     */
    getPrice(asset) {
        return this.prices[asset] || null;
    }

    /**
     * Get all prices
     */
    getAllPrices() {
        return this.prices;
    }

    /**
     * Get assets by category
     */
    getAssetsByCategory(category) {
        return this.assets.filter(asset => {
            const info = this.assetInfo[asset];
            return info && info.category === category;
        });
    }

    /**
     * Add an asset to the ticker
     */
    addAsset(asset) {
        if (!this.assetInfo[asset]) {
            console.warn(`⚠️ Unknown asset: ${asset}`);
            return false;
        }
        if (!this.assets.includes(asset)) {
            this.assets.push(asset);
            this.render();
            this.fetchAllPrices();
            return true;
        }
        return false;
    }

    /**
     * Remove an asset from the ticker
     */
    removeAsset(asset) {
        const index = this.assets.indexOf(asset);
        if (index > -1) {
            this.assets.splice(index, 1);
            delete this.prices[asset];
            this.render();
            return true;
        }
        return false;
    }

    /**
     * Set which assets to display
     */
    setAssets(assets) {
        this.assets = assets.filter(a => this.assetInfo[a]);
        this.render();
        this.fetchAllPrices();
    }

    /**
     * Get all available asset symbols
     */
    getAvailableAssets() {
        return Object.keys(this.assetInfo);
    }

    /**
     * Destroy the ticker bar
     */
    destroy() {
        this.stop();
        const tickerContainer = document.getElementById('ticker-bar');
        if (tickerContainer) {
            tickerContainer.innerHTML = '';
        }
    }
}

// Auto-initialize on DOMContentLoaded
if (typeof window !== 'undefined') {
    window.LiveTickerBar = LiveTickerBar;
}
