/**
 * Odin Bitcoin Trading Dashboard - WebSocket Manager
 */

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.heartbeatInterval = null;
        this.heartbeatTimeout = null;
        this.isConnected = false;
        this.subscriptions = new Set();
        this.messageQueue = [];
        
        // Event handlers
        this.onPriceUpdate = this.onPriceUpdate.bind(this);
        this.onPortfolioUpdate = this.onPortfolioUpdate.bind(this);
        this.onStrategyUpdate = this.onStrategyUpdate.bind(this);
        this.onOrderUpdate = this.onOrderUpdate.bind(this);
        this.onSystemAlert = this.onSystemAlert.bind(this);
        
        // WebSocket URL (adjust based on your setup)
        this.wsUrl = this.getWebSocketUrl();
    }

    /**
     * Get WebSocket URL based on current location
     */
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws`;
    }

    /**
     * Initialize WebSocket connection
     */
    init() {
        this.connect();
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        try {
            console.log('Connecting to WebSocket server...');
            
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = this.onOpen.bind(this);
            this.ws.onmessage = this.onMessage.bind(this);
            this.ws.onclose = this.onClose.bind(this);
            this.ws.onerror = this.onError.bind(this);
            
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.handleReconnect();
        }
    }

    /**
     * Handle WebSocket open event
     */
    onOpen(event) {
        console.log('WebSocket connected successfully');
        
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        
        // Update connection status
        if (window.Dashboard) {
            Dashboard.updateConnectionStatus('connected');
        }
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Send authentication if needed
        this.authenticate();
        
        // Subscribe to default channels
        this.subscribeToDefaults();
        
        // Send queued messages
        this.sendQueuedMessages();
        
        // Notify connection success
        if (window.Dashboard) {
            Dashboard.showNotification(
                'Real-time Connection',
                'Live data stream connected',
                'success',
                3000
            );
        }
    }

    /**
     * Handle WebSocket message event
     */
    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }

    /**
     * Handle WebSocket close event
     */
    onClose(event) {
        console.log('WebSocket connection closed:', event.code, event.reason);
        
        this.isConnected = false;
        this.stopHeartbeat();
        
        // Update connection status
        if (window.Dashboard) {
            Dashboard.updateConnectionStatus('disconnected');
        }
        
        // Handle reconnection if not a clean close
        if (event.code !== 1000) {
            this.handleReconnect();
        }
    }

    /**
     * Handle WebSocket error event
     */
    onError(error) {
        console.error('WebSocket error:', error);
        
        if (window.Dashboard) {
            Dashboard.updateConnectionStatus('disconnected');
        }
    }

    /**
     * Handle incoming messages
     */
    handleMessage(data) {
        if (data.type === 'heartbeat') {
            this.handleHeartbeat(data);
            return;
        }

        switch (data.type) {
            case 'price_update':
                this.onPriceUpdate(data.data);
                break;
                
            case 'portfolio_update':
                this.onPortfolioUpdate(data.data);
                break;
                
            case 'strategy_update':
                this.onStrategyUpdate(data.data);
                break;
                
            case 'order_update':
                this.onOrderUpdate(data.data);
                break;
                
            case 'system_alert':
                this.onSystemAlert(data.data);
                break;
                
            case 'market_data':
                this.onMarketDataUpdate(data.data);
                break;
                
            case 'trade_signal':
                this.onTradeSignal(data.data);
                break;
                
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    /**
     * Handle price updates
     */
    onPriceUpdate(data) {
        if (window.Dashboard) {
            Dashboard.updateBitcoinPrice(data);
        }
        
        // Update price chart if visible
        if (window.ChartManager && window.ChartManager.charts.price) {
            const chart = window.ChartManager.charts.price;
            const newLabel = window.ChartManager.formatChartTime(data.timestamp);
            
            // Add new data point
            chart.data.labels.push(newLabel);
            chart.data.datasets[0].data.push(data.price);
            
            // Keep only last 100 points for performance
            if (chart.data.labels.length > 100) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            
            chart.update('none');
        }
    }

    /**
     * Handle portfolio updates
     */
    onPortfolioUpdate(data) {
        if (window.Dashboard) {
            Dashboard.updatePortfolio(data);
        }
    }

    /**
     * Handle strategy updates
     */
    onStrategyUpdate(data) {
        if (window.Dashboard) {
            Dashboard.updateStrategies([data]);
        }
        
        // Show notification for strategy events
        if (data.event) {
            const eventMessages = {
                'activated': 'Strategy activated',
                'deactivated': 'Strategy deactivated',
                'signal_generated': 'New trading signal generated',
                'trade_executed': 'Trade executed',
                'optimization_complete': 'Parameter optimization completed'
            };
            
            const message = eventMessages[data.event] || `Strategy ${data.event}`;
            
            if (window.Dashboard) {
                Dashboard.showNotification(
                    `${data.name} Strategy`,
                    message,
                    data.event === 'trade_executed' ? 'success' : 'info',
                    5000
                );
            }
        }
    }

    /**
     * Handle order updates
     */
    onOrderUpdate(data) {
        // Update orders table
        if (window.Dashboard) {
            Dashboard.loadOrders();
        }
        
        // Show notification for important order events
        const statusMessages = {
            'filled': { type: 'success', message: 'Order filled successfully' },
            'cancelled': { type: 'warning', message: 'Order cancelled' },
            'rejected': { type: 'error', message: 'Order rejected' },
            'expired': { type: 'warning', message: 'Order expired' }
        };
        
        const statusInfo = statusMessages[data.status];
        if (statusInfo && window.Dashboard) {
            Dashboard.showNotification(
                `Order ${data.status.charAt(0).toUpperCase() + data.status.slice(1)}`,
                `${data.side.toUpperCase()} ${data.amount} BTC - ${statusInfo.message}`,
                statusInfo.type,
                5000
            );
        }
    }

    /**
     * Handle system alerts
     */
    onSystemAlert(data) {
        if (window.Dashboard) {
            Dashboard.showNotification(
                data.title || 'System Alert',
                data.message,
                data.severity || 'info',
                data.duration || 8000
            );
        }
        
        // Handle critical alerts
        if (data.severity === 'critical') {
            // Flash the browser tab
            this.flashBrowserTab();
            
            // Play alert sound if available
            this.playAlertSound();
        }
    }

    /**
     * Handle market data updates
     */
    onMarketDataUpdate(data) {
        // Update market indicators if they exist on the page
        this.updateMarketIndicators(data);
    }

    /**
     * Handle trade signals
     */
    onTradeSignal(data) {
        if (window.Dashboard) {
            Dashboard.showNotification(
                `${data.strategy} Signal`,
                `${data.signal.toUpperCase()} signal at $${data.price.toLocaleString()}`,
                data.signal === 'buy' ? 'success' : 'warning',
                8000
            );
        }
    }

    /**
     * Start heartbeat mechanism
     */
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({
                    type: 'heartbeat',
                    timestamp: Date.now()
                });
                
                // Set timeout for heartbeat response
                this.heartbeatTimeout = setTimeout(() => {
                    console.warn('Heartbeat timeout - connection may be lost');
                    this.disconnect();
                    this.handleReconnect();
                }, 5000);
            }
        }, 30000); // Send heartbeat every 30 seconds
    }

    /**
     * Stop heartbeat mechanism
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }

    /**
     * Handle heartbeat response
     */
    handleHeartbeat(data) {
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }

    /**
     * Send authentication message
     */
    authenticate() {
        // Add authentication logic here if needed
        const authToken = localStorage.getItem('auth_token');
        if (authToken) {
            this.send({
                type: 'authenticate',
                token: authToken
            });
        }
    }

    /**
     * Subscribe to default channels
     */
    subscribeToDefaults() {
        const defaultChannels = [
            'price_updates',
            'portfolio_updates',
            'strategy_updates',
            'order_updates',
            'system_alerts'
        ];
        
        defaultChannels.forEach(channel => {
            this.subscribe(channel);
        });
    }

    /**
     * Subscribe to a channel
     */
    subscribe(channel) {
        if (this.subscriptions.has(channel)) {
            return; // Already subscribed
        }
        
        this.send({
            type: 'subscribe',
            channel: channel
        });
        
        this.subscriptions.add(channel);
        console.log(`Subscribed to channel: ${channel}`);
    }

    /**
     * Unsubscribe from a channel
     */
    unsubscribe(channel) {
        if (!this.subscriptions.has(channel)) {
            return; // Not subscribed
        }
        
        this.send({
            type: 'unsubscribe',
            channel: channel
        });
        
        this.subscriptions.delete(channel);
        console.log(`Unsubscribed from channel: ${channel}`);
    }

    /**
     * Send message to WebSocket server
     */
    send(data) {
        if (this.isConnected && this.ws) {
            try {
                this.ws.send(JSON.stringify(data));
            } catch (error) {
                console.error('Failed to send WebSocket message:', error);
                this.messageQueue.push(data);
            }
        } else {
            // Queue message for when connection is restored
            this.messageQueue.push(data);
        }
    }

    /**
     * Send queued messages
     */
    sendQueuedMessages() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.send(message);
        }
    }

    /**
     * Handle reconnection
     */
    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached. Giving up.');
            if (window.Dashboard) {
                Dashboard.showNotification(
                    'Connection Failed',
                    'Unable to establish real-time connection. Please refresh the page.',
                    'error',
                    0 // Don't auto-dismiss
                );
            }
            return;
        }

        this.reconnectAttempts++;
        
        // Exponential backoff with jitter
        const jitter = Math.random() * 1000;
        const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1) + jitter, this.maxReconnectDelay);
        
        console.log(`Attempting to reconnect in ${Math.round(delay / 1000)} seconds... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        if (window.Dashboard) {
            Dashboard.updateConnectionStatus('connecting');
        }
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }
        
        this.isConnected = false;
        this.stopHeartbeat();
        this.subscriptions.clear();
    }

    /**
     * Update market indicators
     */
    updateMarketIndicators(data) {
        // Update fear & greed index
        const fearGreedElement = document.getElementById('fear-greed-index');
        if (fearGreedElement && data.fear_greed_index) {
            fearGreedElement.textContent = data.fear_greed_index.value;
            fearGreedElement.className = `indicator ${data.fear_greed_index.classification.toLowerCase()}`;
        }
        
        // Update market cap
        const marketCapElement = document.getElementById('market-cap');
        if (marketCapElement && data.market_cap) {
            marketCapElement.textContent = this.formatLargeNumber(data.market_cap);
        }
        
        // Update volume
        const volumeElement = document.getElementById('volume-24h');
        if (volumeElement && data.volume_24h) {
            volumeElement.textContent = this.formatLargeNumber(data.volume_24h);
        }
        
        // Update dominance
        const dominanceElement = document.getElementById('btc-dominance');
        if (dominanceElement && data.btc_dominance) {
            dominanceElement.textContent = `${data.btc_dominance.toFixed(1)}%`;
        }
    }

    /**
     * Flash browser tab for critical alerts
     */
    flashBrowserTab() {
        const originalTitle = document.title;
        let isFlashing = true;
        let flashCount = 0;
        const maxFlashes = 10;
        
        const flashInterval = setInterval(() => {
            if (flashCount >= maxFlashes) {
                document.title = originalTitle;
                clearInterval(flashInterval);
                return;
            }
            
            document.title = isFlashing ? '🚨 ALERT - Odin Dashboard' : originalTitle;
            isFlashing = !isFlashing;
            flashCount++;
        }, 500);
    }

    /**
     * Play alert sound
     */
    playAlertSound() {
        try {
            // Create audio context for alert sound
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2);
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (error) {
            console.warn('Could not play alert sound:', error);
        }
    }

    /**
     * Format large numbers for display
     */
    formatLargeNumber(num) {
        if (num >= 1e12) {
            return (num / 1e12).toFixed(2) + 'T';
        } else if (num >= 1e9) {
            return (num / 1e9).toFixed(2) + 'B';
        } else if (num >= 1e6) {
            return (num / 1e6).toFixed(2) + 'M';
        } else if (num >= 1e3) {
            return (num / 1e3).toFixed(2) + 'K';
        }
        return num.toFixed(2);
    }

    /**
     * Request specific data update
     */
    requestUpdate(dataType, params = {}) {
        this.send({
            type: 'request_update',
            data_type: dataType,
            params: params
        });
    }

    /**
     * Send trading command
     */
    sendTradingCommand(command, params = {}) {
        this.send({
            type: 'trading_command',
            command: command,
            params: params,
            timestamp: Date.now()
        });
    }

    /**
     * Update strategy parameters
     */
    updateStrategyParams(strategyId, params) {
        this.send({
            type: 'update_strategy_params',
            strategy_id: strategyId,
            params: params
        });
    }

    /**
     * Request strategy optimization
     */
    requestOptimization(strategyId, optimizationParams) {
        this.send({
            type: 'optimize_strategy',
            strategy_id: strategyId,
            params: optimizationParams
        });
    }

    /**
     * Get connection status
     */
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            subscriptions: Array.from(this.subscriptions),
            queuedMessages: this.messageQueue.length
        };
    }

    /**
     * Enable/disable specific notifications
     */
    configureNotifications(config) {
        this.send({
            type: 'configure_notifications',
            config: config
        });
    }

    /**
     * Request historical data for charts
     */
    requestHistoricalData(dataType, timeframe, limit = 100) {
        this.send({
            type: 'request_historical_data',
            data_type: dataType,
            timeframe: timeframe,
            limit: limit
        });
    }

    /**
     * Set up custom event listeners
     */
    addEventListener(eventType, callback) {
        document.addEventListener(`ws_${eventType}`, callback);
    }

    /**
     * Remove custom event listeners
     */
    removeEventListener(eventType, callback) {
        document.removeEventListener(`ws_${eventType}`, callback);
    }

    /**
     * Dispatch custom events
     */
    dispatchEvent(eventType, data) {
        const event = new CustomEvent(`ws_${eventType}`, {
            detail: data
        });
        document.dispatchEvent(event);
    }

    /**
     * Handle browser visibility changes
     */
    handleVisibilityChange() {
        if (document.hidden) {
            // Page is hidden, reduce update frequency
            this.send({
                type: 'set_update_frequency',
                frequency: 'low'
            });
        } else {
            // Page is visible, resume normal updates
            this.send({
                type: 'set_update_frequency',
                frequency: 'normal'
            });
            
            // Request fresh data
            this.requestUpdate('all');
        }
    }

    /**
     * Set up network status monitoring
     */
    setupNetworkMonitoring() {
        window.addEventListener('online', () => {
            console.log('Network connection restored');
            if (!this.isConnected) {
                this.connect();
            }
        });
        
        window.addEventListener('offline', () => {
            console.log('Network connection lost');
            if (window.Dashboard) {
                Dashboard.showNotification(
                    'Network Offline',
                    'Internet connection lost. Attempting to reconnect...',
                    'warning'
                );
            }
        });
    }

    /**
     * Initialize WebSocket manager
     */
    static init() {
        if (!window.WebSocketManager) {
            window.WebSocketManager = new WebSocketManager();
        }
        
        // Set up visibility change handler
        document.addEventListener('visibilitychange', () => {
            window.WebSocketManager.handleVisibilityChange();
        });
        
        // Set up network monitoring
        window.WebSocketManager.setupNetworkMonitoring();
        
        // Connect
        window.WebSocketManager.connect();
        
        return window.WebSocketManager;
    }

    /**
     * Cleanup on page unload
     */
    cleanup() {
        this.disconnect();
        this.stopHeartbeat();
        this.messageQueue = [];
        this.subscriptions.clear();
    }
}

// Auto-initialize when script loads
document.addEventListener('DOMContentLoaded', () => {
    WebSocketManager.init();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.WebSocketManager) {
        window.WebSocketManager.cleanup();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketManager;
}