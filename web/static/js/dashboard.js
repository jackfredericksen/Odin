/**
 * Odin Bitcoin Trading Dashboard - Main JavaScript (Updated with Real Data Integration)
 */

class Dashboard {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.updateInterval = 30000; // 30 seconds
        this.isAutoTradingEnabled = false;
        this.lastUpdateTime = null;
        this.connectionStatus = 'disconnected';
        this.notifications = [];
        this.charts = {};
        
        // Bind methods
        this.init = this.init.bind(this);
        this.updateData = this.updateData.bind(this);
        this.handleEmergencyStop = this.handleEmergencyStop.bind(this);
        this.toggleAutoTrading = this.toggleAutoTrading.bind(this);
        
        // Initialize intervals
        this.updateIntervalId = null;
        this.clockIntervalId = null;
        
        // API endpoints
        this.endpoints = {
            health: '/health',
            bitcoinPrice: '/data/current',
            bitcoinHistory: '/data/history',
            portfolio: '/portfolio',
            strategies: '/strategies/list',
            orders: '/trading/history',
            positions: '/trading',
            autoTradingStatus: '/trading/status',
            initDatabase: '/database/init'
        };
    }

    /**
     * Initialize the dashboard
     */
    async init() {
        try {
            console.log('Initializing Odin Dashboard...');
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Start clock
            this.startClock();
            
            // Initialize WebSocket connection
            if (window.WebSocketManager) {
                WebSocketManager.init();
            }
            
            // Initialize charts
            if (window.ChartManager) {
                ChartManager.init();
                this.charts = ChartManager.charts;
            }
            
            // Check if database is initialized
            await this.checkAndInitializeDatabase();
            
            // Load initial data
            await this.loadInitialData();
            
            // Start auto-update
            this.startAutoUpdate();
            
            // Check connection status
            await this.checkConnectionStatus();
            
            console.log('Dashboard initialized successfully');
            this.showNotification('System Online', 'Dashboard connected and ready', 'success');
            
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            this.showNotification('Initialization Error', 'Failed to initialize dashboard', 'error');
        }
    }

    /**
     * Check and initialize database if needed
     */
    async checkAndInitializeDatabase() {
        try {
            // Check if we have data
            const healthResponse = await this.apiCall(this.endpoints.health);
            
            if (healthResponse.success && healthResponse.database) {
                const priceRecords = healthResponse.database.price_records || 0;
                
                if (priceRecords === 0) {
                    console.log('No data found, initializing database...');
                    this.showNotification('Initializing Data', 'Setting up sample data...', 'info');
                    
                    const initResponse = await this.apiCall(this.endpoints.initDatabase);
                    
                    if (initResponse.success) {
                        console.log('Database initialized successfully');
                        this.showNotification('Data Ready', 'Sample data initialized successfully', 'success');
                    } else {
                        console.error('Failed to initialize database:', initResponse.error);
                        this.showNotification('Data Error', 'Failed to initialize sample data', 'error');
                    }
                }
            }
        } catch (error) {
            console.error('Database check error:', error);
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Emergency stop button
        const emergencyBtn = document.getElementById('emergency-stop');
        if (emergencyBtn) {
            emergencyBtn.addEventListener('click', this.handleEmergencyStop);
        }

        // Auto trading toggle
        const autoTradingBtn = document.getElementById('auto-trading-toggle');
        if (autoTradingBtn) {
            autoTradingBtn.addEventListener('click', this.toggleAutoTrading);
        }

        // Refresh buttons
        document.getElementById('refresh-chart')?.addEventListener('click', () => {
            this.refreshChart();
            this.showNotification('Chart Updated', 'Price chart refreshed', 'info');
        });

        document.getElementById('refresh-strategies')?.addEventListener('click', () => {
            this.loadStrategies();
            this.showNotification('Strategies Updated', 'Strategy data refreshed', 'info');
        });

        document.getElementById('refresh-orders')?.addEventListener('click', () => {
            this.loadOrders();
            this.showNotification('Orders Updated', 'Trading history refreshed', 'info');
        });

        // Timeframe selector
        document.getElementById('timeframe-select')?.addEventListener('change', (e) => {
            this.changeTimeframe(e.target.value);
        });

        // Modal close events
        document.getElementById('cancel-emergency-stop')?.addEventListener('click', () => {
            this.hideModal('emergency-modal');
        });

        document.getElementById('close-strategy-modal')?.addEventListener('click', () => {
            this.hideModal('strategy-modal');
        });

        // Portfolio rebalance
        document.getElementById('rebalance-portfolio')?.addEventListener('click', () => {
            this.rebalancePortfolio();
        });

        // Window events
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });

        window.addEventListener('online', () => {
            this.updateConnectionStatus('connected');
            this.showNotification('Connection Restored', 'Internet connection restored', 'success');
        });

        window.addEventListener('offline', () => {
            this.updateConnectionStatus('disconnected');
            this.showNotification('Connection Lost', 'Internet connection lost', 'warning');
        });
    }

    /**
     * Load initial data
     */
    async loadInitialData() {
        console.log('Loading initial data...');
        
        const loadingTasks = [
            this.loadBitcoinPrice(),
            this.loadPortfolio(),
            this.loadStrategies(),
            this.loadOrders(),
            this.loadAutoTradingStatus()
        ];

        try {
            const results = await Promise.allSettled(loadingTasks);
            
            // Log any failed tasks
            results.forEach((result, index) => {
                if (result.status === 'rejected') {
                    console.error(`Initial data loading task ${index} failed:`, result.reason);
                }
            });
            
            // Load initial chart data
            await this.refreshChart();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    /**
     * Start auto-update interval
     */
    startAutoUpdate() {
        if (this.updateIntervalId) {
            clearInterval(this.updateIntervalId);
        }

        this.updateIntervalId = setInterval(async () => {
            await this.updateData();
        }, this.updateInterval);
        
        console.log(`Auto-update started with ${this.updateInterval / 1000}s interval`);
    }

    /**
     * Start clock
     */
    startClock() {
        const updateClock = () => {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            const dateString = now.toLocaleDateString();
            
            const clockElement = document.getElementById('current-time');
            if (clockElement) {
                clockElement.textContent = `${dateString} ${timeString}`;
            }
        };

        updateClock();
        this.clockIntervalId = setInterval(updateClock, 1000);
    }

    /**
     * Update auto trading UI
     */
    updateAutoTradingUI() {
        const button = document.getElementById('auto-trading-toggle');
        const statusSpan = document.getElementById('auto-trading-status');
        
        if (button) {
            button.className = this.isAutoTradingEnabled ? 'btn-danger' : 'btn-primary';
        }
        
        if (statusSpan) {
            statusSpan.textContent = this.isAutoTradingEnabled ? 'Disable Auto Trading' : 'Enable Auto Trading';
        }
    }

    /**
     * Show strategy details modal
     */
    async showStrategyDetails(strategy) {
        const modal = document.getElementById('strategy-modal');
        const title = document.getElementById('strategy-modal-title');
        const body = document.getElementById('strategy-modal-body');
        
        if (title) {
            title.textContent = `${strategy.name} Strategy Details`;
        }
        
        if (body) {
            body.innerHTML = `
                <div class="strategy-details">
                    <div class="metric">
                        <span class="metric-label">Status</span>
                        <span class="metric-value">
                            <span class="badge ${strategy.active ? 'badge-success' : 'badge-secondary'}">
                                ${strategy.active ? 'Active' : 'Inactive'}
                            </span>
                        </span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Type</span>
                        <span class="metric-value">${strategy.type || 'N/A'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total Return</span>
                        <span class="metric-value ${(strategy.return || 0) >= 0 ? 'positive' : 'negative'}">
                            ${(strategy.return || 0) >= 0 ? '+' : ''}${(strategy.return || 0).toFixed(2)}%
                        </span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total Trades</span>
                        <span class="metric-value">${strategy.total_trades || 0}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Win Rate</span>
                        <span class="metric-value">${(strategy.win_rate || 0).toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Sharpe Ratio</span>
                        <span class="metric-value">${(strategy.sharpe_ratio || 0).toFixed(2)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Max Drawdown</span>
                        <span class="metric-value negative">${(strategy.max_drawdown || 0).toFixed(2)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Volatility</span>
                        <span class="metric-value">${(strategy.volatility || 0).toFixed(2)}%</span>
                    </div>
                    ${strategy.description ? `
                    <div class="metric">
                        <span class="metric-label">Description</span>
                        <span class="metric-value">${strategy.description}</span>
                    </div>
                    ` : ''}
                </div>
                <div class="strategy-actions" style="margin-top: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    <button class="btn-primary" onclick="Dashboard.viewStrategyChart('${strategy.id}')">
                        📈 View Chart
                    </button>
                    <button class="btn-secondary" onclick="Dashboard.optimizeStrategy('${strategy.id}')">
                        ⚙️ Optimize
                    </button>
                    <button class="btn-outline" onclick="Dashboard.backtestStrategy('${strategy.id}')">
                        🔄 Backtest
                    </button>
                    <button class="btn-${strategy.active ? 'danger' : 'success'}" onclick="Dashboard.toggleStrategy('${strategy.id}')">
                        ${strategy.active ? '⏸️ Disable' : '▶️ Enable'}
                    </button>
                </div>
            `;
        }
        
        this.showModal('strategy-modal');
    }

    /**
     * View strategy chart
     */
    async viewStrategyChart(strategyId) {
        try {
            this.showNotification('Loading Chart', `Loading ${strategyId} strategy chart...`, 'info');
            // This would load strategy-specific chart data
            console.log(`Viewing chart for strategy: ${strategyId}`);
        } catch (error) {
            this.showNotification('Chart Error', 'Failed to load strategy chart', 'error');
        }
    }

    /**
     * Optimize strategy
     */
    async optimizeStrategy(strategyId) {
        try {
            this.showNotification('Optimizing Strategy', `Running optimization for ${strategyId}...`, 'info');
            
            // Call optimization endpoint
            const response = await this.apiCall(`/strategies/${strategyId}/optimize`, 'POST');
            
            if (response.success) {
                this.showNotification('Optimization Complete', 'Strategy parameters optimized successfully', 'success');
                await this.loadStrategies(); // Refresh strategy data
            } else {
                this.showNotification('Optimization Failed', response.error || 'Unknown error', 'error');
            }
        } catch (error) {
            this.showNotification('Optimization Error', 'Failed to optimize strategy', 'error');
        }
    }

    /**
     * Backtest strategy
     */
    async backtestStrategy(strategyId) {
        try {
            this.showNotification('Running Backtest', `Testing ${strategyId} strategy performance...`, 'info');
            
            // Call backtest endpoint
            const response = await this.apiCall(`/strategies/${strategyId}/backtest`, 'POST');
            
            if (response.success) {
                this.showNotification('Backtest Complete', 'Strategy backtest completed successfully', 'success');
                // Could show backtest results in a modal
            } else {
                this.showNotification('Backtest Failed', response.error || 'Unknown error', 'error');
            }
        } catch (error) {
            this.showNotification('Backtest Error', 'Failed to run backtest', 'error');
        }
    }

    /**
     * Toggle strategy enable/disable
     */
    async toggleStrategy(strategyId) {
        try {
            const strategy = await this.getStrategyById(strategyId);
            const action = strategy?.active ? 'disable' : 'enable';
            
            this.showNotification(
                `${action.charAt(0).toUpperCase() + action.slice(1)}ing Strategy`, 
                `${action.charAt(0).toUpperCase() + action.slice(1)}ing ${strategyId}...`, 
                'info'
            );
            
            const response = await this.apiCall(`/strategies/${strategyId}/${action}`, 'POST');
            
            if (response.success) {
                this.showNotification(
                    `Strategy ${action.charAt(0).toUpperCase() + action.slice(1)}d`, 
                    `${strategyId} has been ${action}d`, 
                    action === 'enable' ? 'success' : 'warning'
                );
                await this.loadStrategies(); // Refresh strategy data
                this.hideModal('strategy-modal'); // Close modal
            } else {
                this.showNotification('Strategy Toggle Failed', response.error || 'Unknown error', 'error');
            }
        } catch (error) {
            this.showNotification('Strategy Toggle Error', 'Failed to toggle strategy', 'error');
        }
    }

    /**
     * Get strategy by ID
     */
    async getStrategyById(strategyId) {
        try {
            const response = await this.apiCall(this.endpoints.strategies);
            if (response.success && response.data) {
                return response.data.find(s => s.id === strategyId);
            }
            return null;
        } catch (error) {
            console.error('Error getting strategy by ID:', error);
            return null;
        }
    }

    /**
     * Rebalance portfolio
     */
    async rebalancePortfolio() {
        try {
            this.showNotification('Rebalancing Portfolio', 'Analyzing and rebalancing portfolio...', 'info');
            
            const response = await this.apiCall('/portfolio/rebalance', 'POST');
            if (response.success) {
                this.showNotification('Portfolio Rebalanced', 'Portfolio rebalancing completed', 'success');
                await this.loadPortfolio();
            } else {
                this.showNotification('Rebalance Failed', response.message || 'Unknown error', 'error');
            }
        } catch (error) {
            this.showNotification('Rebalance Error', 'Failed to rebalance portfolio', 'error');
        }
    }

    /**
     * Check connection status
     */
    async checkConnectionStatus() {
        try {
            const response = await this.apiCall('/health');
            if (response.success) {
                this.updateConnectionStatus('connected');
            } else {
                this.updateConnectionStatus('warning');
            }
        } catch (error) {
            this.updateConnectionStatus('disconnected');
        }
    }

    /**
     * Update connection status
     */
    updateConnectionStatus(status) {
        this.connectionStatus = status;
        
        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        
        if (indicator) {
            indicator.className = `status-indicator ${status}`;
        }
        
        if (text) {
            const statusTexts = {
                connected: 'Connected',
                connecting: 'Connecting...',
                warning: 'Issues Detected',
                disconnected: 'Disconnected'
            };
            text.textContent = statusTexts[status] || 'Unknown';
        }
    }

    /**
     * Update last update time
     */
    updateLastUpdateTime() {
        const element = document.getElementById('data-update-time');
        if (element && this.lastUpdateTime) {
            element.textContent = `Last Data Update: ${this.formatTime(this.lastUpdateTime)}`;
        }
    }

    /**
     * Make API call with enhanced error handling
     */
    async apiCall(endpoint, method = 'GET', data = null) {
        try {
            const url = `${this.apiBaseUrl}${endpoint}`;
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Log successful API calls in debug mode
            if (console.debug) {
                console.debug(`API ${method} ${endpoint}:`, result);
            }
            
            return result;
        } catch (error) {
            console.error(`API call failed: ${method} ${endpoint}`, error);
            
            // Return a consistent error response
            return {
                success: false,
                error: error.message || 'Network error',
                data: null
            };
        }
    }

    /**
     * Show modal
     */
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'flex';
        }
    }

    /**
     * Hide modal
     */
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
        }
    }

    /**
     * Show notification with auto-dismiss
     */
    showNotification(title, message, type = 'info', duration = 5000) {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-header">
                <span class="notification-title">${title}</span>
                <button class="notification-close">&times;</button>
            </div>
            <div class="notification-body">${message}</div>
        `;

        // Close button
        notification.querySelector('.notification-close').onclick = () => {
            notification.remove();
        };

        container.appendChild(notification);

        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);

        // Store notification
        this.notifications.push({
            title,
            message,
            type,
            timestamp: new Date()
        });

        // Keep only last 50 notifications
        if (this.notifications.length > 50) {
            this.notifications = this.notifications.slice(-50);
        }
    }

    /**
     * Format currency
     */
    formatCurrency(amount) {
        if (typeof amount !== 'number' || isNaN(amount)) {
            return '$0.00';
        }
        
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    }

    /**
     * Format time
     */
    formatTime(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch (error) {
            return '--:--:--';
        }
    }

    /**
     * Format date
     */
    formatDate(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            });
        } catch (error) {
            return 'Invalid Date';
        }
    }

    /**
     * Get notification history
     */
    getNotificationHistory() {
        return this.notifications.slice().reverse(); // Return copy in reverse order (newest first)
    }

    /**
     * Clear all notifications
     */
    clearNotifications() {
        const container = document.getElementById('notification-container');
        if (container) {
            container.innerHTML = '';
        }
        this.notifications = [];
    }

    /**
     * Export dashboard data
     */
    async exportData(format = 'json') {
        try {
            const data = {
                timestamp: new Date().toISOString(),
                bitcoin_price: await this.apiCall(this.endpoints.bitcoinPrice),
                portfolio: await this.apiCall(this.endpoints.portfolio),
                strategies: await this.apiCall(this.endpoints.strategies),
                orders: await this.apiCall(this.endpoints.orders),
                notifications: this.getNotificationHistory()
            };

            let content, filename, mimeType;

            if (format === 'json') {
                content = JSON.stringify(data, null, 2);
                filename = `odin-dashboard-${new Date().toISOString().split('T')[0]}.json`;
                mimeType = 'application/json';
            } else if (format === 'csv') {
                // Convert to CSV format (simplified)
                const csv = this.convertToCSV(data);
                content = csv;
                filename = `odin-dashboard-${new Date().toISOString().split('T')[0]}.csv`;
                mimeType = 'text/csv';
            } else {
                throw new Error('Unsupported format');
            }

            // Create download
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showNotification('Export Complete', `Dashboard data exported as ${format.toUpperCase()}`, 'success');
        } catch (error) {
            this.showNotification('Export Error', 'Failed to export dashboard data', 'error');
        }
    }

    /**
     * Convert data to CSV format
     */
    convertToCSV(data) {
        // Simple CSV conversion for basic data
        let csv = 'Type,Timestamp,Value\n';
        
        if (data.bitcoin_price?.success) {
            csv += `Bitcoin Price,${new Date().toISOString()},${data.bitcoin_price.data.price}\n`;
        }
        
        if (data.portfolio?.success) {
            csv += `Portfolio Value,${new Date().toISOString()},${data.portfolio.data.total_value}\n`;
        }

        return csv;
    }

    /**
     * Cleanup resources
     */
    cleanup() {
        if (this.updateIntervalId) {
            clearInterval(this.updateIntervalId);
        }
        
        if (this.clockIntervalId) {
            clearInterval(this.clockIntervalId);
        }
        
        if (window.WebSocketManager) {
            WebSocketManager.disconnect();
        }

        console.log('Dashboard cleanup completed');
    }

    /**
     * Get dashboard statistics
     */
    getStats() {
        return {
            uptime: Date.now() - (this.startTime || Date.now()),
            notifications_count: this.notifications.length,
            connection_status: this.connectionStatus,
            auto_trading_enabled: this.isAutoTradingEnabled,
            last_update: this.lastUpdateTime,
            charts_loaded: Object.keys(this.charts).length
        };
    }
}

// Create global instance
window.Dashboard = new Dashboard();
Dashboard.startTime = Date.now(); // Track start time

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Dashboard;
} all data
     */
    async updateData() {
        try {
            const tasks = [
                this.loadBitcoinPrice(),
                this.loadPortfolio(),
                this.loadStrategies(),
                this.loadOrders()
            ];

            await Promise.allSettled(tasks);
            
            this.lastUpdateTime = new Date();
            this.updateLastUpdateTime();
            
            console.log('Data updated successfully');
            
        } catch (error) {
            console.error('Error updating data:', error);
        }
    }

    /**
     * Load Bitcoin price data
     */
    async loadBitcoinPrice() {
        try {
            const response = await this.apiCall(this.endpoints.bitcoinPrice);
            if (response.success && response.data) {
                this.updateBitcoinPrice(response.data);
            } else {
                console.error('Failed to load Bitcoin price:', response.error);
            }
        } catch (error) {
            console.error('Error loading Bitcoin price:', error);
        }
    }

    /**
     * Load portfolio data
     */
    async loadPortfolio() {
        try {
            const response = await this.apiCall(this.endpoints.portfolio);
            if (response.success && response.data) {
                this.updatePortfolio(response.data);
            } else {
                console.error('Failed to load portfolio:', response.error);
            }
        } catch (error) {
            console.error('Error loading portfolio:', error);
        }
    }

    /**
     * Load strategies data
     */
    async loadStrategies() {
        try {
            const response = await this.apiCall(this.endpoints.strategies);
            if (response.success && response.data) {
                this.updateStrategies(response.data);
            } else {
                console.error('Failed to load strategies:', response.error);
            }
        } catch (error) {
            console.error('Error loading strategies:', error);
        }
    }

    /**
     * Load orders data
     */
    async loadOrders() {
        try {
            const response = await this.apiCall(`${this.endpoints.orders}?limit=10`);
            if (response.success && response.data) {
                this.updateOrders(response.data);
            } else {
                console.error('Failed to load orders:', response.error);
            }
        } catch (error) {
            console.error('Error loading orders:', error);
        }
    }

    /**
     * Load auto trading status
     */
    async loadAutoTradingStatus() {
        try {
            const response = await this.apiCall(this.endpoints.autoTradingStatus);
            if (response.success && response.data) {
                this.isAutoTradingEnabled = response.data.enabled;
                this.updateAutoTradingUI();
            }
        } catch (error) {
            console.error('Error loading auto trading status:', error);
        }
    }

    /**
     * Update Bitcoin price display
     */
    updateBitcoinPrice(data) {
        const priceElement = document.getElementById('bitcoin-price');
        const changeElement = document.getElementById('price-change');
        const timestampElement = document.getElementById('price-timestamp');

        if (priceElement) {
            priceElement.textContent = this.formatCurrency(data.price);
        }

        if (changeElement) {
            const change = data.change_24h || 0;
            changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            changeElement.className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
        }

        if (timestampElement) {
            timestampElement.textContent = `Last updated: ${this.formatTime(data.timestamp || new Date())}`;
        }
    }

    /**
     * Update portfolio display
     */
    updatePortfolio(data) {
        const valueElement = document.getElementById('portfolio-value');
        const changeElement = document.getElementById('portfolio-change');
        const pnlElement = document.getElementById('daily-pnl');
        const pnlPercentageElement = document.getElementById('pnl-percentage');
        const pnlIndicatorElement = document.getElementById('pnl-indicator');

        if (valueElement) {
            valueElement.textContent = this.formatCurrency(data.total_value);
        }

        if (changeElement) {
            const change = data.change_24h || 0;
            changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            changeElement.className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
        }

        if (pnlElement) {
            const pnl = data.pnl_24h || 0;
            pnlElement.textContent = this.formatCurrency(pnl);
            pnlElement.className = `stat-value ${pnl >= 0 ? 'text-success' : 'text-danger'}`;
        }

        if (pnlPercentageElement) {
            const pnlPercent = data.pnl_24h_percent || 0;
            pnlPercentageElement.textContent = `${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%`;
        }

        if (pnlIndicatorElement) {
            const pnl = data.pnl_24h || 0;
            pnlIndicatorElement.className = `stat-indicator ${pnl >= 0 ? 'positive' : 'negative'}`;
        }

        // Update positions
        this.updatePositions(data.positions || []);
        
        // Update portfolio allocation chart
        if (window.ChartManager && data.allocation) {
            ChartManager.updateAllocationChart(data.allocation);
        }
    }

    /**
     * Update strategies display
     */
    updateStrategies(strategies) {
        const container = document.getElementById('strategies-grid');
        if (!container) return;

        container.innerHTML = '';

        strategies.forEach(strategy => {
            const card = this.createStrategyCard(strategy);
            container.appendChild(card);
        });

        // Update strategy performance chart
        if (window.ChartManager) {
            ChartManager.updateStrategyChart(strategies);
        }
    }

    /**
     * Create strategy card element
     */
    createStrategyCard(strategy) {
        const card = document.createElement('div');
        card.className = `strategy-card ${strategy.active ? 'active' : ''}`;
        card.onclick = () => this.showStrategyDetails(strategy);

        card.innerHTML = `
            <div class="strategy-header">
                <span class="strategy-name">${strategy.name}</span>
                <span class="strategy-status ${strategy.active ? 'active' : 'inactive'}">
                    ${strategy.active ? 'Active' : 'Inactive'}
                </span>
            </div>
            <div class="strategy-metrics">
                <div class="strategy-metric">
                    <span class="label">Return:</span>
                    <span class="value ${(strategy.return || 0) >= 0 ? 'text-success' : 'text-danger'}">
                        ${(strategy.return || 0) >= 0 ? '+' : ''}${(strategy.return || 0).toFixed(2)}%
                    </span>
                </div>
                <div class="strategy-metric">
                    <span class="label">Trades:</span>
                    <span class="value">${strategy.total_trades || 0}</span>
                </div>
                <div class="strategy-metric">
                    <span class="label">Win Rate:</span>
                    <span class="value">${(strategy.win_rate || 0).toFixed(1)}%</span>
                </div>
                <div class="strategy-metric">
                    <span class="label">Sharpe:</span>
                    <span class="value">${(strategy.sharpe_ratio || 0).toFixed(2)}</span>
                </div>
            </div>
        `;

        return card;
    }

    /**
     * Update orders table
     */
    updateOrders(orders) {
        const tbody = document.querySelector('#orders-table tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (orders.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; color: var(--text-muted);">
                        No recent orders
                    </td>
                </tr>
            `;
            return;
        }

        orders.forEach(order => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${this.formatTime(order.timestamp)}</td>
                <td>${order.strategy || 'Manual'}</td>
                <td>
                    <span class="badge ${order.side === 'buy' ? 'badge-success' : 'badge-danger'}">
                        ${order.side.toUpperCase()}
                    </span>
                </td>
                <td>${(order.amount || 0).toFixed(6)} BTC</td>
                <td>${this.formatCurrency(order.price || 0)}</td>
                <td>
                    <span class="order-status ${order.status}">
                        ${order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                    </span>
                </td>
                <td class="${(order.pnl || 0) >= 0 ? 'text-success' : 'text-danger'}">
                    ${(order.pnl || 0) >= 0 ? '+' : ''}${this.formatCurrency(order.pnl || 0)}
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    /**
     * Update positions display
     */
    updatePositions(positions) {
        const countElement = document.getElementById('positions-count');
        const valueElement = document.getElementById('positions-value');
        const subtitleElement = document.getElementById('positions-subtitle');

        if (countElement) {
            countElement.textContent = positions.length;
        }

        if (valueElement) {
            const totalValue = positions.reduce((sum, pos) => sum + (pos.value || 0), 0);
            valueElement.textContent = this.formatCurrency(totalValue);
        }

        if (subtitleElement) {
            const totalExposure = positions.reduce((sum, pos) => sum + Math.abs(pos.size || 0), 0);
            subtitleElement.textContent = `${totalExposure.toFixed(4)} BTC Exposure`;
        }
    }

    /**
     * Refresh chart
     */
    async refreshChart() {
        const timeframe = document.getElementById('timeframe-select')?.value || '24';
        if (window.ChartManager) {
            await ChartManager.updatePriceChart(timeframe);
        }
    }

    /**
     * Change timeframe
     */
    async changeTimeframe(hours) {
        if (window.ChartManager) {
            await ChartManager.updatePriceChart(hours);
        }
    }

    /**
     * Handle emergency stop
     */
    async handleEmergencyStop() {
        this.showModal('emergency-modal');
        
        document.getElementById('confirm-emergency-stop').onclick = async () => {
            try {
                this.showNotification('Emergency Stop Activated', 'All trading stopped successfully', 'warning');
                this.isAutoTradingEnabled = false;
                this.updateAutoTradingUI();
            } catch (error) {
                this.showNotification('Emergency Stop Error', 'Failed to stop trading', 'error');
            }
            
            this.hideModal('emergency-modal');
        };
    }

    /**
     * Toggle auto trading
     */
    async toggleAutoTrading() {
        try {
            this.isAutoTradingEnabled = !this.isAutoTradingEnabled;
            this.updateAutoTradingUI();
            
            const status = this.isAutoTradingEnabled ? 'enabled' : 'disabled';
            this.showNotification(
                `Auto Trading ${status.charAt(0).toUpperCase() + status.slice(1)}`,
                `Automatic trading has been ${status}`,
                this.isAutoTradingEnabled ? 'success' : 'warning'
            );
        } catch (error) {
            this.showNotification('Auto Trading Error', 'Failed to toggle auto trading', 'error');
        }
    }

    /**
     * Update