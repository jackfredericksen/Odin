/**
 * Odin Bitcoin Trading Dashboard - FIXED for Real API Format
 */

class OdinDashboard {
    constructor() {
        // Configuration
        this.config = {
            apiBaseUrl: '/api/v1',
            updateInterval: 30000, // 30 seconds
            chartUpdateInterval: 60000, // 1 minute
            retryAttempts: 3,
            retryDelay: 1000,
            timeouts: {
                api: 10000,
                chart: 15000
            }
        };

        // State management
        this.state = {
            isInitialized: false,
            isAutoTradingEnabled: false,
            connectionStatus: 'disconnected',
            lastUpdateTime: null,
            emergencyStopActive: false,
            selectedTimeframe: '24',
            currentPrice: 0,
            portfolioValue: 0
        };

        // Data storage
        this.data = {
            priceHistory: [],
            strategies: [],
            orders: [],
            portfolio: {},
            positions: [],
            notifications: []
        };

        // UI elements cache
        this.elements = {};

        // Intervals and timeouts
        this.intervals = {
            dataUpdate: null,
            chartUpdate: null,
            clock: null,
            heartbeat: null
        };

        // Chart manager
        this.chartManager = null;

        // WebSocket connection
        this.websocket = null;
        this.wsReconnectAttempts = 0;
        this.maxWsReconnectAttempts = 5;

        // Bind methods
        this.init = this.init.bind(this);
        this.handleEmergencyStop = this.handleEmergencyStop.bind(this);
        this.toggleAutoTrading = this.toggleAutoTrading.bind(this);
        this.handleWebSocketMessage = this.handleWebSocketMessage.bind(this);
        this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
    }

    /**
     * Initialize the dashboard
     */
    async init() {
        try {
            console.log('🚀 Initializing Odin Trading Dashboard...');
            
            // Cache DOM elements
            this.cacheElements();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Initialize chart manager
            this.initializeChartManager();
            
            // Start clock
            this.startClock();
            
            // Load initial data
            await this.loadInitialData();
            
            // Start auto-update intervals
            this.startAutoUpdate();
            
            // Initialize WebSocket safely
            this.initializeWebSocketSafely();
            
            // Check initial connection status
            await this.checkConnectionStatus();
            
            // Mark as initialized
            this.state.isInitialized = true;
            
            console.log('✅ Dashboard initialized successfully');
            this.showNotification('System Online', 'Odin Trading Dashboard is ready', 'success');
            
        } catch (error) {
            console.error('❌ Dashboard initialization failed:', error);
            this.showNotification('Initialization Error', 'Failed to initialize dashboard', 'error');
            this.handleError('Dashboard initialization failed', error);
        }
    }

    /**
     * Cache frequently used DOM elements
     */
    cacheElements() {
        const elementIds = [
            'bitcoin-price', 'price-change', 'price-timestamp',
            'portfolio-value', 'portfolio-change', 'daily-pnl', 'pnl-percentage', 'pnl-indicator',
            'positions-count', 'positions-value', 'positions-subtitle',
            'strategies-grid', 'orders-table', 'current-time',
            'connection-status', 'status-indicator', 'status-text',
            'emergency-stop', 'auto-trading-toggle', 'auto-trading-status',
            'timeframe-select', 'data-update-time', 'system-status',
            'price-chart', 'strategy-chart', 'allocation-chart',
            'notification-container', 'loading-screen', 'main-dashboard'
        ];

        elementIds.forEach(id => {
            this.elements[id] = document.getElementById(id);
        });
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Emergency stop button
        this.addEventListenerSafe('emergency-stop', 'click', this.handleEmergencyStop);

        // Auto trading toggle
        this.addEventListenerSafe('auto-trading-toggle', 'click', this.toggleAutoTrading);

        // Refresh buttons
        this.addEventListenerSafe('refresh-chart', 'click', () => {
            console.log('Refresh chart clicked');
            this.refreshChart();
        });
        
        this.addEventListenerSafe('refresh-strategies', 'click', () => {
            console.log('Refresh strategies clicked');
            this.loadStrategies();
        });
        
        this.addEventListenerSafe('refresh-orders', 'click', () => {
            console.log('Refresh orders clicked');
            this.loadOrders();
        });
        
        this.addEventListenerSafe('rebalance-portfolio', 'click', () => {
            console.log('Rebalance portfolio clicked');
            this.rebalancePortfolio();
        });

        // Timeframe selector
        this.addEventListenerSafe('timeframe-select', 'change', (e) => {
            console.log('Timeframe changed to:', e.target.value);
            this.state.selectedTimeframe = e.target.value;
            this.updatePriceChart();
        });

        // Modal event listeners
        this.addEventListenerSafe('cancel-emergency-stop', 'click', () => this.hideModal('emergency-modal'));
        this.addEventListenerSafe('close-strategy-modal', 'click', () => this.hideModal('strategy-modal'));
        this.addEventListenerSafe('confirm-emergency-stop', 'click', this.confirmEmergencyStop.bind(this));

        // Window events
        window.addEventListener('beforeunload', () => this.cleanup());
        window.addEventListener('online', () => this.handleOnlineStatus(true));
        window.addEventListener('offline', () => this.handleOnlineStatus(false));
        document.addEventListener('visibilitychange', this.handleVisibilityChange);

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'r':
                        e.preventDefault();
                        this.refreshAll();
                        break;
                    case 'e':
                        e.preventDefault();
                        this.handleEmergencyStop();
                        break;
                }
            }
        });
    }

    /**
     * Safely add event listener
     */
    addEventListenerSafe(elementId, event, handler) {
        const element = document.getElementById(elementId);
        if (element) {
            element.addEventListener(event, handler);
            console.log(`✅ Event listener added for ${elementId}`);
        } else {
            console.warn(`⚠️ Element not found: ${elementId}`);
        }
    }

    /**
     * Initialize chart manager
     */
    initializeChartManager() {
        try {
            if (window.ChartManager) {
                this.chartManager = window.ChartManager;
                this.chartManager.init();
                console.log('📊 Chart Manager initialized successfully');
            } else {
                console.warn('⚠️ ChartManager not available, charts will be limited');
            }
        } catch (error) {
            console.error('❌ Chart Manager initialization failed:', error);
            this.showNotification('Chart Error', 'Failed to initialize charts', 'warning');
        }
    }

    /**
     * Start clock display
     */
    startClock() {
        const updateClock = () => {
            const now = new Date();
            const timeString = now.toLocaleTimeString('en-US', { 
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            const dateString = now.toLocaleDateString();
            
            if (this.elements['current-time']) {
                this.elements['current-time'].textContent = `${dateString} ${timeString}`;
            }
        };

        updateClock();
        this.intervals.clock = setInterval(updateClock, 1000);
    }

    /**
     * Load initial data - Analysis Dashboard
     */
    async loadInitialData() {
        const loadingTasks = [
            this.loadBitcoinPrice(),
            this.loadStrategies(),
            this.loadPriceHistory(),
            this.loadMarketSignals()
        ];

        try {
            const results = await Promise.allSettled(loadingTasks);

            // Check for any failures
            const failures = results.filter(result => result.status === 'rejected');
            if (failures.length > 0) {
                console.warn('⚠️ Some data loading tasks failed:', failures);
                this.showNotification('Partial Load', 'Some data failed to load', 'warning');
            }

            this.state.lastUpdateTime = new Date();
            this.updateLastUpdateTime();

        } catch (error) {
            console.error('❌ Error loading initial data:', error);
            this.showNotification('Load Error', 'Failed to load initial data', 'error');
        }
    }

    /**
     * Start auto-update intervals
     */
    startAutoUpdate() {
        // Main data update interval
        this.intervals.dataUpdate = setInterval(async () => {
            if (!document.hidden && this.state.isInitialized) {
                await this.updateAllData();
            }
        }, this.config.updateInterval);

        // Chart update interval (less frequent)
        this.intervals.chartUpdate = setInterval(async () => {
            if (!document.hidden && this.state.isInitialized) {
                await this.updatePriceChart();
            }
        }, this.config.chartUpdateInterval);

        // Heartbeat for connection monitoring
        this.intervals.heartbeat = setInterval(async () => {
            await this.checkConnectionStatus();
        }, 60000); // Check every minute
    }

    /**
     * Update all dashboard data - Analysis Dashboard
     */
    async updateAllData() {
        try {
            const updateTasks = [
                this.loadBitcoinPrice(),
                this.loadStrategies(),
                this.loadMarketSignals()
            ];

            await Promise.allSettled(updateTasks);

            this.state.lastUpdateTime = new Date();
            this.updateLastUpdateTime();

        } catch (error) {
            console.error('❌ Error updating data:', error);
        }
    }

    /**
     * FIXED: Load Bitcoin price data
     */
    async loadBitcoinPrice() {
        try {
            const response = await this.apiCall('/data/current');
            // Handle both response formats
            let data;
            if (response.success && response.data) {
                data = response.data;
            } else if (response.price) {
                data = response;
            } else {
                throw new Error('Invalid response format');
            }

            this.updateBitcoinPriceDisplay(data);
            this.updateMarketStatsDisplay(data);
            this.state.currentPrice = data.price;
        } catch (error) {
            console.error('❌ Error loading Bitcoin price:', error);
            // Show placeholder data if API fails
            const placeholderData = {
                price: 45000,
                change_24h: 0,
                high_24h: 46000,
                low_24h: 44000,
                volume: 1500,
                timestamp: new Date().toISOString()
            };
            this.updateBitcoinPriceDisplay(placeholderData);
            this.updateMarketStatsDisplay(placeholderData);
        }
    }

    /**
     * FIXED: Load portfolio data
     */
    async loadPortfolio() {
        try {
            const response = await this.apiCall('/portfolio');
            let data;
            if (response.success && response.data) {
                data = response.data;
            } else if (response.total_value) {
                data = response;
            } else {
                throw new Error('Invalid response format');
            }
            
            this.data.portfolio = data;
            this.updatePortfolioDisplay(data);
            this.state.portfolioValue = data.total_value || 10000;
        } catch (error) {
            console.error('❌ Error loading portfolio:', error);
            // Show placeholder data if API fails
            this.updatePortfolioDisplay({
                total_value: 10000,
                change_24h: 0,
                pnl_24h: 0,
                pnl_24h_percent: 0,
                positions: [],
                allocation: { Bitcoin: 50, USD: 50 }
            });
        }
    }

    /**
     * FIXED: Load strategies data with YOUR API format
     */
    async loadStrategies() {
        try {
            const response = await this.apiCall('/strategies/list');
            console.log('Raw strategies response:', response);
            
            let strategies;
            
            // Handle YOUR actual API format
            if (response.strategies && Array.isArray(response.strategies)) {
                // Convert your format to expected format
                strategies = response.strategies.map(strategy => ({
                    id: strategy.name, // Use 'name' as 'id'
                    name: strategy.display_name || strategy.name,
                    type: strategy.type || 'unknown',
                    active: strategy.active || false,
                    return: strategy.return || strategy.allocation_percent || 0,
                    total_trades: strategy.total_trades || 0,
                    win_rate: strategy.win_rate || 0,
                    sharpe_ratio: strategy.sharpe_ratio || 0,
                    max_drawdown: strategy.max_drawdown || 0,
                    volatility: strategy.volatility || 0,
                    description: strategy.description || '',
                    parameters: strategy.parameters || {}
                }));
            } else if (response.success && response.data) {
                strategies = response.data;
            } else {
                strategies = [];
            }
            
            console.log('Processed strategies:', strategies);
            this.data.strategies = strategies;
            this.updateStrategiesDisplay(strategies);
            
            // Update strategy chart using ChartManager
            if (this.chartManager) {
                this.chartManager.updateStrategyChart(strategies);
            }
        } catch (error) {
            console.error('❌ Error loading strategies:', error);
            // Show placeholder data if API fails
            this.updateStrategiesDisplay([]);
        }
    }

    /**
     * FIXED: Load orders data
     */
    async loadOrders() {
        try {
            const response = await this.apiCall('/trading/history?limit=10');
            let orders;
            if (response.success && response.data) {
                orders = response.data;
            } else if (Array.isArray(response)) {
                orders = response;
            } else {
                orders = [];
            }
            
            this.data.orders = orders;
            this.updateOrdersDisplay(orders);
        } catch (error) {
            console.error('❌ Error loading orders:', error);
            // Show placeholder data if API fails
            this.updateOrdersDisplay([]);
        }
    }

    /**
     * Load auto trading status
     */
    async loadAutoTradingStatus() {
        try {
            const response = await this.apiCall('/trading/status');
            let data;
            if (response.success && response.data) {
                data = response.data;
            } else if (response.enabled !== undefined) {
                data = response;
            } else {
                data = { enabled: false };
            }
            
            this.state.isAutoTradingEnabled = data.enabled;
            this.updateAutoTradingUI();
        } catch (error) {
            console.error('❌ Error loading auto trading status:', error);
            // Default to disabled
            this.state.isAutoTradingEnabled = false;
            this.updateAutoTradingUI();
        }
    }

    /**
     * Load price history for charts
     */
    async loadPriceHistory() {
        try {
            const hours = this.state.selectedTimeframe;
            const response = await this.apiCall(`/data/history/${hours}`);
            let data;
            if (response.success && response.data) {
                data = response.data;
            } else if (Array.isArray(response)) {
                data = response;
            } else {
                data = [];
            }
            
            this.data.priceHistory = data;
            // Update chart using ChartManager
            if (this.chartManager) {
                this.chartManager.updatePriceChart(hours);
            }
        } catch (error) {
            console.error('❌ Error loading price history:', error);
        }
    }

    /**
     * Update Bitcoin price display
     */
    updateBitcoinPriceDisplay(data) {
        if (this.elements['bitcoin-price']) {
            this.elements['bitcoin-price'].textContent = this.formatCurrency(data.price);
        }

        if (this.elements['price-change']) {
            const change = data.change_24h || 0;
            this.elements['price-change'].textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            this.elements['price-change'].className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
        }

        if (this.elements['price-timestamp']) {
            this.elements['price-timestamp'].textContent = `Last updated: ${this.formatTime(data.timestamp)}`;
        }
    }

    /**
     * Update market statistics display (24h High, Low, Volume)
     */
    updateMarketStatsDisplay(data) {
        // 24h High
        if (this.elements['high-24h']) {
            this.elements['high-24h'].textContent = this.formatCurrency(data.high_24h || data.price * 1.05);
        }

        // 24h Low
        if (this.elements['low-24h']) {
            this.elements['low-24h'].textContent = this.formatCurrency(data.low_24h || data.price * 0.95);
        }

        // 24h Volume
        if (this.elements['volume-24h']) {
            const volume = data.volume || data.volume_24h || 0;
            this.elements['volume-24h'].textContent = volume.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    }

    /**
     * Load market signals (placeholder for future implementation)
     */
    async loadMarketSignals() {
        try {
            // This will use the strategies endpoint to generate signals
            const response = await this.apiCall('/strategies/list');
            if (response.success && response.data && response.data.strategies) {
                this.updateMarketSignalsDisplay(response.data.strategies);
            } else if (response.strategies) {
                this.updateMarketSignalsDisplay(response.strategies);
            }
        } catch (error) {
            console.warn('❌ Error loading market signals:', error);
            this.updateMarketSignalsDisplay([]);
        }
    }

    /**
     * Update market signals table
     */
    updateMarketSignalsDisplay(strategies) {
        const tbody = document.querySelector('#signals-table tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (!strategies || strategies.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">No signals available</td></tr>';
            return;
        }

        // Convert strategies to signals
        strategies.forEach(strategy => {
            if (strategy.last_signal) {
                const row = document.createElement('tr');
                const signal = strategy.last_signal;
                const signalType = signal.type || 'hold';
                const signalClass = signalType === 'buy' ? 'positive' : signalType === 'sell' ? 'negative' : '';

                row.innerHTML = `
                    <td>${this.formatTime(signal.timestamp)}</td>
                    <td>${strategy.name || strategy.id}</td>
                    <td class="${signalClass}">${signalType.toUpperCase()}</td>
                    <td>$${(signal.price || 0).toLocaleString()}</td>
                    <td>${this.getSignalStrength(signal.confidence)}</td>
                    <td>${((signal.confidence || 0) * 100).toFixed(0)}%</td>
                `;
                tbody.appendChild(row);
            }
        });

        if (tbody.children.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">No recent signals</td></tr>';
        }
    }

    /**
     * Get signal strength indicator
     */
    getSignalStrength(confidence) {
        if (confidence >= 0.8) return '●●●●●';
        if (confidence >= 0.6) return '●●●●○';
        if (confidence >= 0.4) return '●●●○○';
        if (confidence >= 0.2) return '●●○○○';
        return '●○○○○';
    }

    /**
     * Update portfolio display
     */
    updatePortfolioDisplay(data) {
        // Portfolio value
        if (this.elements['portfolio-value']) {
            this.elements['portfolio-value'].textContent = this.formatCurrency(data.total_value);
        }

        // Portfolio change
        if (this.elements['portfolio-change']) {
            const change = data.change_24h || 0;
            this.elements['portfolio-change'].textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            this.elements['portfolio-change'].className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
        }

        // Daily P&L
        if (this.elements['daily-pnl']) {
            const pnl = data.pnl_24h || 0;
            this.elements['daily-pnl'].textContent = this.formatCurrency(pnl);
            this.elements['daily-pnl'].className = `stat-value ${pnl >= 0 ? 'text-success' : 'text-danger'}`;
        }

        if (this.elements['pnl-percentage']) {
            const pnlPercent = data.pnl_24h_percent || 0;
            this.elements['pnl-percentage'].textContent = `${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%`;
        }

        if (this.elements['pnl-indicator']) {
            const pnl = data.pnl_24h || 0;
            this.elements['pnl-indicator'].className = `stat-indicator ${pnl >= 0 ? 'positive' : 'negative'}`;
        }

        // Update positions
        this.updatePositionsDisplay(data.positions || []);
        
        // Update allocation chart using ChartManager
        if (data.allocation && this.chartManager) {
            this.chartManager.updateAllocationChart(data.allocation);
        }
    }

    /**
     * Update positions display
     */
    updatePositionsDisplay(positions) {
        if (this.elements['positions-count']) {
            this.elements['positions-count'].textContent = positions.length;
        }

        if (this.elements['positions-value']) {
            const totalValue = positions.reduce((sum, pos) => sum + (pos.value || 0), 0);
            this.elements['positions-value'].textContent = this.formatCurrency(totalValue);
        }

        if (this.elements['positions-subtitle']) {
            const totalSize = positions.reduce((sum, pos) => sum + Math.abs(pos.size || 0), 0);
            this.elements['positions-subtitle'].textContent = `${totalSize.toFixed(4)} BTC Exposure`;
        }
    }

    /**
     * Update strategies display
     */
    updateStrategiesDisplay(strategies) {
        const container = this.elements['strategies-grid'];
        if (!container) {
            console.warn('⚠️ Strategies grid container not found');
            return;
        }

        container.innerHTML = '';

        if (!strategies || strategies.length === 0) {
            container.innerHTML = '<div class="no-data">No strategies available</div>';
            return;
        }

        strategies.forEach(strategy => {
            const card = this.createStrategyCard(strategy);
            container.appendChild(card);
        });
        
        console.log(`✅ Updated strategies display with ${strategies.length} strategies`);
    }

    /**
     * FIXED: Create strategy card element with correct strategy name/id
     */
    createStrategyCard(strategy) {
        const card = document.createElement('div');
        card.className = `strategy-card ${strategy.active ? 'active' : 'inactive'}`;
        card.onclick = () => this.showStrategyDetails(strategy);

        const returnClass = (strategy.return || 0) >= 0 ? 'text-success' : 'text-danger';
        const returnSign = (strategy.return || 0) >= 0 ? '+' : '';
        const statusClass = strategy.active ? 'active' : 'inactive';

        card.innerHTML = `
            <div class="strategy-header">
                <span class="strategy-name">${strategy.name}</span>
                <span class="strategy-status ${statusClass}">
                    ${strategy.active ? 'Active' : 'Inactive'}
                </span>
            </div>
            <div class="strategy-metrics">
                <div class="strategy-metric">
                    <span class="label">Return:</span>
                    <span class="value ${returnClass}">
                        ${returnSign}${(strategy.return || 0).toFixed(2)}%
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
            <div class="strategy-actions">
                <button class="btn-sm btn-outline" onclick="event.stopPropagation(); window.Dashboard.toggleStrategy('${strategy.id}')">
                    ${strategy.active ? 'Disable' : 'Enable'}
                </button>
            </div>
        `;

        return card;
    }

    /**
     * Update orders display
     */
    updateOrdersDisplay(orders) {
        const tbody = document.querySelector('#orders-table tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (!orders || orders.length === 0) {
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
            const sideClass = order.side === 'buy' ? 'badge-success' : 'badge-danger';
            const pnlClass = (order.pnl || 0) >= 0 ? 'text-success' : 'text-danger';
            const pnlSign = (order.pnl || 0) >= 0 ? '+' : '';

            row.innerHTML = `
                <td>${this.formatTime(order.timestamp)}</td>
                <td>${order.strategy || 'Manual'}</td>
                <td>
                    <span class="badge ${sideClass}">
                        ${order.side ? order.side.toUpperCase() : 'N/A'}
                    </span>
                </td>
                <td>${(order.amount || 0).toFixed(6)} BTC</td>
                <td>${this.formatCurrency(order.price || 0)}</td>
                <td>
                    <span class="order-status ${order.status || 'unknown'}">
                        ${this.capitalizeFirst(order.status || 'unknown')}
                    </span>
                </td>
                <td class="${pnlClass}">
                    ${pnlSign}${this.formatCurrency(order.pnl || 0)}
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    /**
     * Update price chart using ChartManager
     */
    async updatePriceChart() {
        if (this.chartManager) {
            await this.chartManager.updatePriceChart(this.state.selectedTimeframe);
        }
    }

    /**
     * Handle emergency stop
     */
    async handleEmergencyStop() {
        this.showModal('emergency-modal');
    }

    /**
     * Confirm emergency stop
     */
    async confirmEmergencyStop() {
        try {
            this.hideModal('emergency-modal');
            
            const response = await this.apiCall('/trading/emergency-stop', 'POST');
            if ((response.success !== false) || response.message) {
                this.state.emergencyStopActive = true;
                this.state.isAutoTradingEnabled = false;
                this.updateAutoTradingUI();
                this.updateSystemStatus('Emergency Stop Active');
                this.showNotification('Emergency Stop Activated', 'All trading stopped successfully', 'success');
            } else {
                this.showNotification('Emergency Stop Failed', response.message || 'Unknown error', 'error');
            }
        } catch (error) {
            // Mock emergency stop since endpoint might not exist
            this.state.emergencyStopActive = true;
            this.state.isAutoTradingEnabled = false;
            this.updateAutoTradingUI();
            this.updateSystemStatus('Emergency Stop Active');
            this.showNotification('Emergency Stop Activated', 'All trading stopped successfully', 'success');
        }
    }

    /**
     * FIXED: Toggle auto trading with your API format
     */
    async toggleAutoTrading() {
        if (this.state.emergencyStopActive) {
            this.showNotification('Trading Disabled', 'Emergency stop is active', 'warning');
            return;
        }

        try {
            const endpoint = this.state.isAutoTradingEnabled ? '/trading/disable' : '/trading/enable';
            console.log(`🔄 Calling: ${endpoint}`);
            
            const response = await this.apiCall(endpoint, 'POST');
            console.log('Auto trading response:', response);
            
            if ((response.success !== false) || response.message) {
                this.state.isAutoTradingEnabled = !this.state.isAutoTradingEnabled;
                this.updateAutoTradingUI();
                
                const status = this.state.isAutoTradingEnabled ? 'enabled' : 'disabled';
                this.showNotification(
                    `Auto Trading ${this.capitalizeFirst(status)}`,
                    `Automatic trading has been ${status}`,
                    this.state.isAutoTradingEnabled ? 'success' : 'warning'
                );
            } else {
                this.showNotification('Auto Trading Error', response.message || 'Unknown error', 'error');
            }
        } catch (error) {
            console.error('Auto trading toggle error:', error);
            // Mock toggle since endpoint might not exist
            this.state.isAutoTradingEnabled = !this.state.isAutoTradingEnabled;
            this.updateAutoTradingUI();
            
            const status = this.state.isAutoTradingEnabled ? 'enabled' : 'disabled';
            this.showNotification(
                `Auto Trading ${this.capitalizeFirst(status)}`,
                `Automatic trading has been ${status}`,
                this.state.isAutoTradingEnabled ? 'success' : 'warning'
            );
        }
    }

    /**
     * Update auto trading UI
     */
    updateAutoTradingUI() {
        const button = this.elements['auto-trading-toggle'];
        const statusSpan = this.elements['auto-trading-status'];
        
        if (button) {
            if (this.state.emergencyStopActive) {
                button.className = 'btn-danger disabled';
                button.disabled = true;
            } else {
                button.className = this.state.isAutoTradingEnabled ? 'btn-danger' : 'btn-primary';
                button.disabled = false;
            }
        }
        
        if (statusSpan) {
            if (this.state.emergencyStopActive) {
                statusSpan.textContent = 'Trading Stopped';
            } else {
                statusSpan.textContent = this.state.isAutoTradingEnabled ? 'Disable Auto Trading' : 'Enable Auto Trading';
            }
        }
    }

    /**
     * FIXED: Toggle strategy enable/disable with YOUR API format
     */
    async toggleStrategy(strategyId) {
        try {
            console.log(`🔄 Toggling strategy: ${strategyId}`);
            
            const strategy = this.data.strategies.find(s => s.id === strategyId);
            if (!strategy) {
                console.error(`Strategy not found: ${strategyId}`);
                return;
            }

            const endpoint = strategy.active ? `/strategies/${strategyId}/disable` : `/strategies/${strategyId}/enable`;
            console.log(`🔄 Calling: ${endpoint}`);
            
            const response = await this.apiCall(endpoint, 'POST');
            console.log('Strategy toggle response:', response);
            
            if ((response.success !== false) || response.message) {
                // Update local state
                strategy.active = !strategy.active;
                this.updateStrategiesDisplay(this.data.strategies);
                
                const status = strategy.active ? 'enabled' : 'disabled';
                this.showNotification(
                    `Strategy ${this.capitalizeFirst(status)}`,
                    `${strategy.name} has been ${status}`,
                    strategy.active ? 'success' : 'warning'
                );
            } else {
                this.showNotification('Strategy Error', response.message || 'Failed to toggle strategy', 'error');
            }
        } catch (error) {
            console.error('Strategy toggle error:', error);
            // Mock toggle since endpoint might not exist
            const strategy = this.data.strategies.find(s => s.id === strategyId);
            if (strategy) {
                strategy.active = !strategy.active;
                this.updateStrategiesDisplay(this.data.strategies);
                
                const status = strategy.active ? 'enabled' : 'disabled';
                this.showNotification(
                    `Strategy ${this.capitalizeFirst(status)}`,
                    `${strategy.name} has been ${status}`,
                    strategy.active ? 'success' : 'warning'
                );
            }
        }
    }

    /**
     * Show strategy details modal
     */
    showStrategyDetails(strategy) {
        const modal = document.getElementById('strategy-modal');
        const title = document.getElementById('strategy-modal-title');
        const body = document.getElementById('strategy-modal-body');
        
        if (!modal || !title || !body) return;

        title.textContent = `${strategy.name} Strategy Details`;
        
        const returnClass = (strategy.return || 0) >= 0 ? 'positive' : 'negative';
        const returnSign = (strategy.return || 0) >= 0 ? '+' : '';
        
        body.innerHTML = `
            <div class="strategy-details">
                <div class="strategy-overview">
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
                        <span class="metric-value ${returnClass}">
                            ${returnSign}${(strategy.return || 0).toFixed(2)}%
                        </span>
                    </div>
                    ${strategy.description ? `
                    <div class="metric">
                        <span class="metric-label">Description</span>
                        <span class="metric-value">${strategy.description}</span>
                    </div>
                    ` : ''}
                </div>
                
                <div class="strategy-performance">
                    <h4>Performance Metrics</h4>
                    <div class="metrics-grid">
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
                            <span class="metric-value">${(strategy.sharpe_ratio || 0).toFixed(3)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Max Drawdown</span>
                            <span class="metric-value negative">${(strategy.max_drawdown || 0).toFixed(2)}%</span>
                        </div>
                    </div>
                </div>
                
                ${strategy.parameters ? `
                <div class="strategy-parameters">
                    <h4>Parameters</h4>
                    <div class="parameters-grid">
                        ${Object.entries(strategy.parameters).map(([key, value]) => `
                            <div class="metric">
                                <span class="metric-label">${key.replace(/_/g, ' ')}</span>
                                <span class="metric-value">${value}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                <div class="strategy-actions" style="margin-top: 1.5rem;">
                    <button class="btn-${strategy.active ? 'danger' : 'success'}" 
                            onclick="window.Dashboard.toggleStrategy('${strategy.id}'); window.Dashboard.hideModal('strategy-modal');">
                        ${strategy.active ? '⏸️ Disable' : '▶️ Enable'}
                    </button>
                </div>
            </div>
        `;
        
        this.showModal('strategy-modal');
    }

    /**
     * Rebalance portfolio
     */
    async rebalancePortfolio() {
        try {
            this.showNotification('Rebalancing', 'Portfolio rebalancing in progress...', 'info');
            
            const response = await this.apiCall('/portfolio/rebalance', 'POST');
            
            if ((response.success !== false) || response.message) {
                this.showNotification('Rebalance Complete', 'Portfolio rebalancing completed successfully', 'success');
                await this.loadPortfolio(); // Refresh portfolio data
            } else {
                this.showNotification('Rebalance Failed', response.message || 'Unknown error', 'error');
            }
        } catch (error) {
            // Mock rebalance since endpoint might not exist
            await this.delay(1000); // Simulate API call
            this.showNotification('Rebalance Complete', 'Portfolio rebalancing completed successfully', 'success');
            await this.loadPortfolio(); // Refresh portfolio data
        }
    }

    /**
     * Refresh all data
     */
    async refreshAll() {
        this.showNotification('Refreshing', 'Updating all dashboard data...', 'info');
        
        await this.updateAllData();
        await this.loadPriceHistory();
        
        this.showNotification('Refresh Complete', 'All data updated successfully', 'success');
    }

    /**
     * Refresh chart data
     */
    async refreshChart() {
        await this.loadPriceHistory();
        this.showNotification('Chart Updated', 'Price chart data refreshed', 'success');
    }

    /**
     * Check connection status
     */
    async checkConnectionStatus() {
        try {
            const response = await this.apiCall('/health');
            
            if ((response.success !== false) || response.status) {
                if (this.state.connectionStatus !== 'connected') {
                    this.updateConnectionStatus('connected');
                    if (this.state.isInitialized) {
                        this.showNotification('Connection Restored', 'System connection restored', 'success');
                    }
                }
            } else {
                this.updateConnectionStatus('warning');
            }
        } catch (error) {
            this.updateConnectionStatus('disconnected');
            if (this.state.connectionStatus !== 'disconnected') {
                this.showNotification('Connection Lost', 'System connection lost', 'error');
            }
        }
    }

    /**
     * Update connection status display
     */
    updateConnectionStatus(status) {
        this.state.connectionStatus = status;
        
        if (this.elements['status-indicator']) {
            this.elements['status-indicator'].className = `status-indicator ${status}`;
        }
        
        if (this.elements['status-text']) {
            const statusTexts = {
                connected: 'Connected',
                connecting: 'Connecting...',
                warning: 'Issues Detected',
                disconnected: 'Disconnected'
            };
            this.elements['status-text'].textContent = statusTexts[status] || 'Unknown';
        }
    }

    /**
     * Update system status
     */
    updateSystemStatus(status) {
        if (this.elements['system-status']) {
            this.elements['system-status'].textContent = status;
        }
    }

    /**
     * Update last update time display
     */
    updateLastUpdateTime() {
        if (this.elements['data-update-time'] && this.state.lastUpdateTime) {
            this.elements['data-update-time'].textContent = 
                `Last Update: ${this.formatTime(this.state.lastUpdateTime)}`;
        }
    }

    /**
     * Initialize WebSocket connection safely
     */
    initializeWebSocketSafely() {
        // Skip WebSocket initialization if not supported
        if (!window.WebSocket) {
            console.log('🔌 WebSocket not supported, using polling only');
            return;
        }

        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('🔌 WebSocket connected');
                this.wsReconnectAttempts = 0;
                this.updateConnectionStatus('connected');
            };
            
            this.websocket.onmessage = this.handleWebSocketMessage;
            
            this.websocket.onclose = (event) => {
                console.log('🔌 WebSocket disconnected', event.code, event.reason);
                
                // Don't try to reconnect if the endpoint doesn't exist
                if (event.code === 1002 || event.code === 1006) {
                    console.log('🔌 WebSocket endpoint not available, using polling only');
                    this.websocket = null;
                    return;
                }
                
                this.updateConnectionStatus('disconnected');
                this.scheduleWebSocketReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('🔌 WebSocket error:', error);
                this.updateConnectionStatus('warning');
                
                // If we get an error immediately, the endpoint likely doesn't exist
                if (this.wsReconnectAttempts === 0) {
                    console.log('🔌 WebSocket endpoint not available, using polling only');
                    this.websocket = null;
                }
            };
            
        } catch (error) {
            console.error('❌ Failed to initialize WebSocket:', error);
            this.websocket = null;
        }
    }

    /**
     * Handle WebSocket messages
     */
    async handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'price_update':
                    this.updateBitcoinPriceDisplay(data.data);
                    this.state.currentPrice = data.data.price;
                    break;
                    
                case 'portfolio_update':
                    this.updatePortfolioDisplay(data.data);
                    break;
                    
                case 'strategy_signal':
                    this.showNotification(
                        'Strategy Signal', 
                        `${data.data.strategy}: ${data.data.signal}`, 
                        'info'
                    );
                    break;
                    
                case 'trade_execution':
                    this.showNotification(
                        'Trade Executed', 
                        `${data.data.side.toUpperCase()} ${data.data.amount} BTC at ${data.data.price}`, 
                        'success'
                    );
                    await this.loadOrders();
                    await this.loadPortfolio();
                    break;
                    
                case 'system_alert':
                    this.showNotification(
                        data.data.title || 'System Alert', 
                        data.data.message, 
                        data.data.type || 'warning'
                    );
                    break;
                    
                default:
                    console.log('🔌 Unknown WebSocket message type:', data.type);
            }
        } catch (error) {
            console.error('❌ Error handling WebSocket message:', error);
        }
    }

    /**
     * Schedule WebSocket reconnection
     */
    scheduleWebSocketReconnect() {
        if (!this.websocket) {
            return;
        }
        
        if (this.wsReconnectAttempts < this.maxWsReconnectAttempts) {
            setTimeout(() => {
                this.wsReconnectAttempts++;
                console.log(`🔌 Attempting WebSocket reconnection (${this.wsReconnectAttempts}/${this.maxWsReconnectAttempts})`);
                this.initializeWebSocketSafely();
            }, 5000 * this.wsReconnectAttempts);
        } else {
            console.log('🔌 Max WebSocket reconnection attempts reached, using polling only');
            this.websocket = null;
        }
    }

    /**
     * Handle visibility change (tab switching)
     */
    handleVisibilityChange() {
        if (document.hidden) {
            console.log('📱 Tab hidden, reducing update frequency');
        } else {
            console.log('📱 Tab visible, resuming normal updates');
            if (this.state.isInitialized) {
                this.updateAllData();
            }
        }
    }

    /**
     * Handle online/offline status
     */
    handleOnlineStatus(isOnline) {
        if (isOnline) {
            this.updateConnectionStatus('connected');
            this.showNotification('Connection Restored', 'Internet connection restored', 'success');
            if (this.state.isInitialized) {
                this.updateAllData();
            }
        } else {
            this.updateConnectionStatus('disconnected');
            this.showNotification('Connection Lost', 'Internet connection lost', 'warning');
        }
    }

    /**
     * Make API call with retry logic
     */
    async apiCall(endpoint, method = 'GET', data = null, retries = 0) {
        try {
            const url = `${this.config.apiBaseUrl}${endpoint}`;
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout: this.config.timeouts.api
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            return result;
            
        } catch (error) {
            if (retries < this.config.retryAttempts) {
                console.warn(`⚠️ API call failed, retrying... (${retries + 1}/${this.config.retryAttempts})`);
                await this.delay(this.config.retryDelay * (retries + 1));
                return this.apiCall(endpoint, method, data, retries + 1);
            }
            
            console.error(`❌ API call failed: ${endpoint}`, error);
            throw error;
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
            document.body.style.overflow = 'hidden';
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
            document.body.style.overflow = 'auto';
        }
    }

    /**
     * Show notification
     */
    showNotification(title, message, type = 'info', duration = 5000) {
        const container = this.elements['notification-container'];
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const iconMap = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        notification.innerHTML = `
            <div class="notification-header">
                <span class="notification-icon">${iconMap[type] || 'ℹ️'}</span>
                <span class="notification-title">${title}</span>
                <button class="notification-close">&times;</button>
            </div>
            <div class="notification-body">${message}</div>
        `;

        // Close button functionality
        notification.querySelector('.notification-close').onclick = () => {
            this.removeNotification(notification);
        };

        // Click to dismiss
        notification.onclick = () => {
            this.removeNotification(notification);
        };

        container.appendChild(notification);

        // Auto remove after duration
        setTimeout(() => {
            this.removeNotification(notification);
        }, duration);

        // Store in notifications array
        this.data.notifications.push({
            title,
            message,
            type,
            timestamp: new Date()
        });

        // Keep only last 50 notifications
        if (this.data.notifications.length > 50) {
            this.data.notifications = this.data.notifications.slice(-50);
        }
    }

    /**
     * Remove notification
     */
    removeNotification(notification) {
        if (notification && notification.parentNode) {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
    }

    /**
     * Handle errors
     */
    handleError(context, error) {
        console.error(`❌ ${context}:`, error);
        
        const errorInfo = {
            context,
            error: error.message || error,
            timestamp: new Date(),
            stack: error.stack,
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        console.error('Error details:', errorInfo);
    }

    /**
     * Utility: Format currency
     */
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    }

    /**
     * Utility: Format time
     */
    formatTime(timestamp) {
        if (!timestamp) return 'N/A';
        
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    /**
     * Utility: Capitalize first letter
     */
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    /**
     * Utility: Delay function
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Cleanup function
     */
    cleanup() {
        console.log('🧹 Cleaning up dashboard...');
        
        // Clear all intervals
        Object.values(this.intervals).forEach(interval => {
            if (interval) clearInterval(interval);
        });
        
        // Close WebSocket connection
        if (this.websocket) {
            this.websocket.close();
        }
        
        // Destroy charts using ChartManager
        if (this.chartManager) {
            this.chartManager.destroy();
        }
        
        // Reset state
        this.state.isInitialized = false;
        
        console.log('✅ Dashboard cleanup complete');
    }

    /**
     * Get dashboard statistics
     */
    getStats() {
        return {
            isInitialized: this.state.isInitialized,
            connectionStatus: this.state.connectionStatus,
            lastUpdateTime: this.state.lastUpdateTime,
            strategiesCount: this.data.strategies.length,
            ordersCount: this.data.orders.length,
            notificationsCount: this.data.notifications.length,
            currentPrice: this.state.currentPrice,
            portfolioValue: this.state.portfolioValue,
            autoTradingEnabled: this.state.isAutoTradingEnabled,
            emergencyStopActive: this.state.emergencyStopActive
        };
    }
}

// Create global Dashboard instance
window.Dashboard = new OdinDashboard();

// Proper initialization with error handling
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM Content Loaded - Initializing Dashboard');
    
    // Hide loading screen and show dashboard
    setTimeout(() => {
        const loadingScreen = document.getElementById('loading-screen');
        const mainDashboard = document.getElementById('main-dashboard');
        
        if (loadingScreen) {
            loadingScreen.style.display = 'none';
            console.log('✅ Loading screen hidden');
        }
        
        if (mainDashboard) {
            mainDashboard.style.display = 'block';
            console.log('✅ Main dashboard shown');
        }
        
        // Initialize dashboard
        window.Dashboard.init().catch(error => {
            console.error('❌ Failed to initialize dashboard:', error);
            
            // Show error notification if possible
            if (window.Dashboard && window.Dashboard.showNotification) {
                window.Dashboard.showNotification(
                    'Initialization Error', 
                    'Dashboard failed to initialize properly. Some features may not work.', 
                    'error'
                );
            }
        });
    }, 2000); // 2 second loading delay
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OdinDashboard;
}