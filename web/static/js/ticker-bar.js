/**
 * Live Ticker Bar - Bloomberg-style multi-coin price ticker
 * Displays real-time prices for all 7 supported coins
 */

class LiveTickerBar {
    constructor(coins = ['BTC', 'ETH', 'SOL', 'XRP', 'BNB', 'SUI', 'HYPE']) {
        this.coins = coins;
        this.prices = {};
        this.updateInterval = 5000; // 5 seconds
        this.intervalId = null;
        this.apiBase = '/api/v1';

        // Coin display info
        this.coinInfo = {
            'BTC': { name: 'Bitcoin', symbol: '₿', color: '#f7931a' },
            'ETH': { name: 'Ethereum', symbol: 'Ξ', color: '#627eea' },
            'SOL': { name: 'Solana', symbol: '◎', color: '#00d4aa' },
            'XRP': { name: 'XRP', symbol: '✕', color: '#23292f' },
            'BNB': { name: 'BNB', symbol: '🔶', color: '#f3ba2f' },
            'SUI': { name: 'Sui', symbol: '〜', color: '#4da2ff' },
            'HYPE': { name: 'Hyperliquid', symbol: '🚀', color: '#00d4ff' }
        };
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
     * Fetch prices for all coins in parallel
     */
    async fetchAllPrices() {
        try {
            const promises = this.coins.map(coin =>
                fetch(`${this.apiBase}/data/price?symbol=${coin}`)
                    .then(res => res.json())
                    .then(result => {
                        // Handle API response format
                        const data = result.success && result.data ? result.data : result;
                        return { coin, data };
                    })
                    .catch(err => {
                        console.warn(`⚠️ Failed to fetch ${coin} price:`, err);
                        return { coin, data: null };
                    })
            );

            const results = await Promise.all(promises);

            // Update prices object
            results.forEach(({ coin, data }) => {
                if (data && data.price) {
                    // Calculate change_percent if not provided
                    let change_percent = data.change_percent || data.change_24h || 0;

                    this.prices[coin] = {
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
     * Render the ticker bar HTML
     */
    render() {
        const tickerContainer = document.getElementById('ticker-bar');
        if (!tickerContainer) {
            console.warn('⚠️ Ticker bar container not found');
            return;
        }

        let html = '';

        this.coins.forEach(coin => {
            const info = this.coinInfo[coin];
            html += `
                <div class="ticker-item" data-coin="${coin}">
                    <span class="ticker-symbol" style="color: ${info.color}">${info.symbol} ${coin}</span>
                    <span class="ticker-price" id="ticker-price-${coin}">$---.--</span>
                    <span class="ticker-change" id="ticker-change-${coin}">
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
        this.coins.forEach(coin => {
            const priceData = this.prices[coin];
            if (!priceData) return;

            // Update price
            const priceEl = document.getElementById(`ticker-price-${coin}`);
            if (priceEl) {
                const formattedPrice = this.formatPrice(priceData.price);
                priceEl.textContent = `$${formattedPrice}`;

                // Add flash animation on price change
                priceEl.classList.add('ticker-flash');
                setTimeout(() => priceEl.classList.remove('ticker-flash'), 500);
            }

            // Update change
            const changeEl = document.getElementById(`ticker-change-${coin}`);
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
     * Format price based on value
     */
    formatPrice(price) {
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
     * Get current price for a coin
     */
    getPrice(coin) {
        return this.prices[coin] || null;
    }

    /**
     * Get all prices
     */
    getAllPrices() {
        return this.prices;
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
