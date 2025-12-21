/**
 * TradingView Advanced Charts Integration
 * Provides professional-grade charting with full technical analysis
 */

class TradingViewWidget {
    constructor(containerId = 'tradingview_chart') {
        this.containerId = containerId;
        this.widget = null;
        this.currentSymbol = 'BTCUSD';
        this.currentInterval = '60'; // 1 hour default
        
        //  Symbol mappings for TradingView
        this.symbolMappings = {
            'BTC': 'BINANCE:BTCUSDT',
            'ETH': 'BINANCE:ETHUSDT',
            'SOL': 'BINANCE:SOLUSDT',
            'XRP': 'BINANCE:XRPUSDT',
            'BNB': 'BINANCE:BNBUSDT',
            'SUI': 'BINANCE:SUIUSDT',
            'HYPE': 'HYPERLIQUID:HYPEUSDT' // Fallback to similar
        };
        
        // Timeframe mappings (hours to TradingView intervals)
        this.intervalMappings = {
            1: '1',      // 1 hour = 1 minute
            4: '5',      // 4 hours = 5 minutes  
            12: '15',    // 12 hours = 15 minutes
            24: '60',    // 24 hours = 1 hour
            168: 'D',    // 7 days = Daily
            720: 'D',    // 30 days = Daily
            2160: 'W'    // 90 days = Weekly
        };
    }

    /**
     * Initialize TradingView widget
     */
    init(symbol = 'BTC', timeframe = 24) {
        console.log(`📊 Initializing TradingView widget for ${symbol} (${timeframe}h)`);
        
        this.updateChart(symbol, timeframe);
    }

    /**
     * Update chart with new symbol/timeframe
     */
    updateChart(symbol, timeframe = 24) {
        const tvSymbol = this.symbolMappings[symbol] || 'BINANCE:BTCUSDT';
        const interval = this.intervalMappings[timeframe] || '60';
        
        console.log(`📊 Updating TradingView: ${tvSymbol}, interval: ${interval}`);
        
        // Clear existing widget
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`❌ TradingView container #${this.containerId} not found`);
            return;
        }
        
        container.innerHTML = '';
        
        // Create new widget
        try {
            this.widget = new TradingView.widget({
                "width": "100%",
                "height": "100%",
                "symbol": tvSymbol,
                "interval": interval,
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#0a0e27",
                "enable_publishing": false,
                "hide_side_toolbar": false,
                "allow_symbol_change": true,
                "details": true,
                "hotlist": true,
                "calendar": true,
                "studies": [
                    "STD;SMA",
                    "STD;EMA",
                    "STD;Volume",
                    "STD;RSI",
                    "STD;MACD"
                ],
                "container_id": this.containerId,
                "show_popup_button": true,
                "popup_width": "1000",
                "popup_height": "650"
            });
            
            console.log('✅ TradingView widget created');
            this.currentSymbol = symbol;
            
        } catch (error) {
            console.error('❌ Error creating TradingView widget:', error);
        }
    }

    /**
     * Switch to different coin
     */
    switchCoin(symbol) {
        console.log(`🔄 Switching TradingView chart to ${symbol}`);
        // Get current timeframe from dashboard if available
        const timeframe = window.dashboard ? window.dashboard.selectedTimeframe : 24;
        this.updateChart(symbol, timeframe);
    }

    /**
     * Switch timeframe
     */
    switchTimeframe(hours) {
        console.log(`🕐 Switching TradingView timeframe to ${hours}h`);
        this.updateChart(this.currentSymbol, hours);
    }

    /**
     * Destroy widget
     */
    destroy() {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.innerHTML = '';
        }
        this.widget = null;
        console.log('🗑️ TradingView widget destroyed');
    }
}

// Make available globally
if (typeof window !== 'undefined') {
    window.TradingViewWidget = TradingViewWidget;
}
