/**
 * Odin Bitcoin Trading Dashboard - Complete JavaScript Implementation
 * 
 * Production-ready dashboard for the Odin Bitcoin trading bot with real-time
 * data updates, interactive charts, portfolio management, and strategy monitoring.
 * 
 * Features:
 * - Real-time price and portfolio updates
 * - Interactive trading charts with multiple timeframes
 * - Strategy performance monitoring and management
 * - Portfolio allocation and rebalancing
 * - Emergency trading controls
 * - WebSocket integration for live data
 * - Comprehensive error handling and notifications
 * 
 * Author: Odin Development Team
 * License: MIT
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

        // Charts
        this.charts = {
            price: null,
            strategy: null,
            allocation: null
        };

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
            
            // Initialize charts
            await this.initializeCharts();
            
            // Start clock
            this.startClock();
            
            // Load initial data
            await this.loadInitialData();
            
            // Start auto-update intervals
            this.startAutoUpdate();
            
            // Initialize WebSocket connection
            this.initializeWebSocket();
            
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
        if (this.elements['emergency-stop']) {
            this.elements['emergency-stop'].addEventListener('click', this.handleEmergencyStop);
        }

        // Auto trading toggle
        if (this.elements['auto-trading-toggle']) {
            this.elements['auto-trading-toggle'].addEventListener('click', this.toggleAutoTrading);
        }

        // Refresh buttons
        this.addEventListenerSafe('refresh-chart', 'click', () => this.refreshChart());
        this.addEventListenerSafe('refresh-strategies', 'click', () => this.loadStrategies());
        this.addEventListenerSafe('refresh-orders', 'click', () => this.loadOrders());
        this.addEventListenerSafe('rebalance-portfolio', 'click', () => this.rebalancePortfolio());

        // Timeframe selector
        if (this.elements['timeframe-select']) {
            this.elements['timeframe-select'].addEventListener('change', (e) => {
                this.state.selectedTimeframe = e.target.value;
                this.updatePriceChart();
            });
        }

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
        }
    }

    /**
     * Initialize Chart.js charts
     */
    async initializeCharts() {
        try {
            // Price Chart
            if (this.elements['price-chart']) {
                this.charts.price = new Chart(this.elements['price-chart'], {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Bitcoin Price (USD)',
                            data: [],
                            borderColor: '#f39c12',
                            backgroundColor: 'rgba(243, 156, 18, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            intersect: false,
                            mode: 'index'
                        },
                        plugins: {
                            legend: {
                                display: true,
                                labels: { color: '#ffffff' }
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleColor: '#ffffff',
                                bodyColor: '#ffffff',
                                borderColor: '#f39c12',
                                borderWidth: 1
                            }
                        },
                        scales: {
                            x: {
                                display: true,
                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                ticks: { color: '#ffffff' }
                            },
                            y: {
                                display: true,
                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                ticks: { 
                                    color: '#ffffff',
                                    callback: function(value) {
                                        return '$' + value.toLocaleString();
                                    }
                                }
                            }
                        }
                    }
                });
            }

            // Strategy Performance Chart
            if (this.elements['strategy-chart']) {
                this.charts.strategy = new Chart(this.elements['strategy-chart'], {
                    type: 'bar',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Return (%)',
                            data: [],
                            backgroundColor: [],
                            borderColor: [],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleColor: '#ffffff',
                                bodyColor: '#ffffff'
                            }
                        },
                        scales: {
                            x: {
                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                ticks: { color: '#ffffff' }
                            },
                            y: {
                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                ticks: { 
                                    color: '#ffffff',
                                    callback: function(value) {
                                        return value + '%';
                                    }
                                }
                            }
                        }
                    }
                });
            }

            // Portfolio Allocation Chart
            if (this.elements['allocation-chart']) {
                this.charts.allocation = new Chart(this.elements['allocation-chart'], {
                    type: 'doughnut',
                    data: {
                        labels: ['Bitcoin', 'USD'],
                        datasets: [{
                            data: [50, 50],
                            backgroundColor: ['#f39c12', '#3498db'],
                            borderColor: ['#e67e22', '#2980b9'],
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { color: '#ffffff' }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleColor: '#ffffff',
                                bodyColor: '#ffffff',
                                callbacks: {
                                    label: function(context) {
                                        return context.label + ': ' + context.parsed + '%';
                                    }
                                }
                            }
                        }
                    }
                });
            }

            console.log('📊 Charts initialized successfully');
        } catch (error) {
            console.error('❌ Chart initialization failed:', error);
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
     * Load initial data
     */
    async loadInitialData() {
        const loadingTasks = [
            this.loadBitcoinPrice(),
            this.loadPortfolio(),
            this.loadStrategies(),
            this.loadOrders(),
            this.loadAutoTradingStatus(),
            this.loadPriceHistory()
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
     * Update all dashboard data
     */
    async updateAllData() {
        try {
            const updateTasks = [
                this.loadBitcoinPrice(),
                this.loadPortfolio(),
                this.loadStrategies(),
                this.loadOrders()
            ];

            await Promise.allSettled(updateTasks);
            
            this.state.lastUpdateTime = new Date();
            this.updateLastUpdateTime();
            
        } catch (error) {
            console.error('❌ Error updating data:', error);
        }
    }

    /**
     * Load Bitcoin price data
     */
    async loadBitcoinPrice() {
        try {
            const response = await this.apiCall('/data/current');
            if (response.success && response.data) {
                this.updateBitcoinPriceDisplay(response.data);
                this.state.currentPrice = response.data.price;
            }
        } catch (error) {
            console.error('❌ Error loading Bitcoin price:', error);
        }
    }

    /**
     * Load portfolio data
     */
    async loadPortfolio() {
        try {
            const response = await this.apiCall('/portfolio');
            if (response.success && response.data) {
                this.data.portfolio = response.data;
                this.updatePortfolioDisplay(response.data);
                this.state.portfolioValue = response.data.total_value;
            }
        } catch (error) {
            console.error('❌ Error loading portfolio:', error);
        }
    }

    /**
     * Load strategies data
     */
    async loadStrategies() {
        try {
            const response = await this.apiCall('/strategies/list');
            if (response.success && response.data) {
                this.data.strategies = response.data;
                this.updateStrategiesDisplay(response.data);
                this.updateStrategyChart(response.data);
            }
        } catch (error) {
            console.error('❌ Error loading strategies:', error);
        }
    }

    /**
     * Load orders data
     */
    async loadOrders() {
        try {
            const response = await this.apiCall('/trading/history?limit=10');
            if (response.success && response.data) {
                this.data.orders = response.data;
                this.updateOrdersDisplay(response.data);
            }
        } catch (error) {
            console.error('❌ Error loading orders:', error);
        }
    }

    /**
     * Load auto trading status
     */
    async loadAutoTradingStatus() {
        try {
            const response = await this.apiCall('/trading/status');
            if (response.success && response.data) {
                this.state.isAutoTradingEnabled = response.data.enabled;
                this.updateAutoTradingUI();
            }
        } catch (error) {
            console.error('❌ Error loading auto trading status:', error);
        }
    }

    /**
     * Load price history for charts
     */
    async loadPriceHistory() {
        try {
            const hours = this.state.selectedTimeframe;
            const response = await this.apiCall(`/data/history/${hours}`);
            if (response.success && response.data) {
                this.data.priceHistory = response.data;
                this.updatePriceChart();
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
        
        // Update allocation chart
        if (data.allocation && this.charts.allocation) {
            this.updateAllocationChart(data.allocation);
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
        if (!container) return;

        container.innerHTML = '';

        if (!strategies || strategies.length === 0) {
            container.innerHTML = '<div class="no-data">No strategies available</div>';
            return;
        }

        strategies.forEach(strategy => {
            const card = this.createStrategyCard(strategy);
            container.appendChild(card);
        });
    }

    /**
     * Create strategy card element
     */
    createStrategyCard(strategy) {
        const card = document.createElement('div');
        card.className = `strategy-card ${strategy.active ? 'active' : 'inactive'}`;
        card.onclick = () => this.showStrategyDetails(strategy);

        const returnClass = strategy.return >= 0 ? 'text-success' : 'text-danger';
        const returnSign = strategy.return >= 0 ? '+' : '';
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
                        ${returnSign}${strategy.return.toFixed(2)}%
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
            const pnlClass = order.pnl >= 0 ? 'text-success' : 'text-danger';
            const pnlSign = order.pnl >= 0 ? '+' : '';

            row.innerHTML = `
                <td>${this.formatTime(order.timestamp)}</td>
                <td>${order.strategy || 'Manual'}</td>
                <td>
                    <span class="badge ${sideClass}">
                        ${order.side.toUpperCase()}
                    </span>
                </td>
                <td>${order.amount.toFixed(6)} BTC</td>
                <td>${this.formatCurrency(order.price)}</td>
                <td>
                    <span class="order-status ${order.status}">
                        ${this.capitalizeFirst(order.status)}
                    </span>
                </td>
                <td class="${pnlClass}">
                    ${pnlSign}${this.formatCurrency(order.pnl)}
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    /**
     * Update price chart
     */
    updatePriceChart() {
        if (!this.charts.price || !this.data.priceHistory) return;

        const labels = this.data.priceHistory.map(item => 
            new Date(item.timestamp).toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
            })
        );
        
        const prices = this.data.priceHistory.map(item => item.price);

        this.charts.price.data.labels = labels;
        this.charts.price.data.datasets[0].data = prices;
        this.charts.price.update('none');
    }

    /**
     * Update strategy chart
     */
    updateStrategyChart(strategies) {
        if (!this.charts.strategy || !strategies) return;

        const labels = strategies.map(s => s.name);
        const returns = strategies.map(s => s.return);
        const colors = returns.map(r => r >= 0 ? '#27ae60' : '#e74c3c');

        this.charts.strategy.data.labels = labels;
        this.charts.strategy.data.datasets[0].data = returns;
        this.charts.strategy.data.datasets[0].backgroundColor = colors;
        this.charts.strategy.data.datasets[0].borderColor = colors;
        this.charts.strategy.update('none');
    }

    /**
     * Update allocation chart
     */
    updateAllocationChart(allocation) {
        if (!this.charts.allocation || !allocation) return;

        const btcPercentage = allocation.Bitcoin || 0;
        const usdPercentage = allocation.USD || 0;

        this.charts.allocation.data.datasets[0].data = [btcPercentage, usdPercentage];
        this.charts.allocation.update('none');
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
            if (response.success) {
                this.state.emergencyStopActive = true;
                this.state.isAutoTradingEnabled = false;
                this.updateAutoTradingUI();
                this.updateSystemStatus('Emergency Stop Active');
                this.showNotification('Emergency Stop Activated', 'All trading stopped successfully', 'success');
            } else {
                this.showNotification('Emergency Stop Failed', response.message || 'Unknown error', 'error');
            }
        } catch (error) {
            this.showNotification('Emergency Stop Error', 'Failed to stop trading', 'error');
            this.handleError('Emergency stop failed', error);
        }
    }

    /**
     * Toggle auto trading
     */
    async toggleAutoTrading() {
        if (this.state.emergencyStopActive) {
            this.showNotification('Trading Disabled', 'Emergency stop is active', 'warning');
            return;
        }

        try {
            const endpoint = this.state.isAutoTradingEnabled ? '/trading/disable' : '/trading/enable';
            const response = await this.apiCall(endpoint, 'POST');
            
            if (response.success) {
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
            this.showNotification('Auto Trading Error', 'Failed to toggle auto trading', 'error');
            this.handleError('Auto trading toggle failed', error);
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
     * Toggle strategy enable/disable
     */
    async toggleStrategy(strategyId) {
        try {
            const strategy = this.data.strategies.find(s => s.id === strategyId);
            if (!strategy) return;

            const endpoint = strategy.active ? `/strategies/${strategyId}/disable` : `/strategies/${strategyId}/enable`;
            const response = await this.apiCall(endpoint, 'POST');
            
            if (response.success) {
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
            this.showNotification('Strategy Error', 'Failed to toggle strategy', 'error');
            this.handleError('Strategy toggle failed', error);
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
        
        const returnClass = strategy.return >= 0 ? 'positive' : 'negative';
        const returnSign = strategy.return >= 0 ? '+' : '';
        
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
                            ${returnSign}${strategy.return.toFixed(2)}%
                        </span>
                    </div>
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
                        <div class="metric">
                            <span class="metric-label">Volatility</span>
                            <span class="metric-value">${(strategy.volatility || 0).toFixed(2)}%</span>
                        </div>
                    </div>
                </div>
                
                <div class="strategy-actions" style="margin-top: 1.5rem;">
                    <button class="btn-primary" onclick="window.Dashboard.viewStrategyChart('${strategy.id}')">
                        📊 View Chart
                    </button>
                    <button class="btn-secondary" onclick="window.Dashboard.optimizeStrategy('${strategy.id}')">
                        ⚙️ Optimize
                    </button>
                    <button class="btn-outline" onclick="window.Dashboard.backtestStrategy('${strategy.id}')">
                        📈 Backtest
                    </button>
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
     * View strategy chart
     */
    async viewStrategyChart(strategyId) {
        try {
            const hours = this.state.selectedTimeframe;
            const response = await this.apiCall(`/strategies/${strategyId}/chart/${hours}`);
            
            if (response.success && response.data) {
                // This would open a detailed chart modal or redirect to a chart page
                this.showNotification('Chart Loading', 'Loading strategy chart...', 'info');
                // Implementation depends on your chart requirements
            }
        } catch (error) {
            this.showNotification('Chart Error', 'Failed to load strategy chart', 'error');
        }
    }

    /**
     * Optimize strategy
     */
    async optimizeStrategy(strategyId) {
        try {
            this.showNotification('Optimization Started', 'Strategy optimization in progress...', 'info');
            
            const response = await this.apiCall(`/strategies/${strategyId}/optimize`, 'POST');
            
            if (response.success) {
                this.showNotification('Optimization Complete', 'Strategy optimization completed successfully', 'success');
                await this.loadStrategies(); // Refresh strategies
            } else {
                this.showNotification('Optimization Failed', response.message || 'Unknown error', 'error');
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
            this.showNotification('Backtest Started', 'Running strategy backtest...', 'info');
            
            const hours = this.state.selectedTimeframe;
            const response = await this.apiCall(`/strategies/${strategyId}/backtest/${hours}`, 'POST');
            
            if (response.success) {
                this.showNotification('Backtest Complete', 'Strategy backtest completed', 'success');
                // Could show backtest results in a modal or new page
            } else {
                this.showNotification('Backtest Failed', response.message || 'Unknown error', 'error');
            }
        } catch (error) {
            this.showNotification('Backtest Error', 'Failed to run backtest', 'error');
        }
    }

    /**
     * Rebalance portfolio
     */
    async rebalancePortfolio() {
        try {
            this.showNotification('Rebalancing', 'Portfolio rebalancing in progress...', 'info');
            
            const response = await this.apiCall('/portfolio/rebalance', 'POST');
            
            if (response.success) {
                this.showNotification('Rebalance Complete', 'Portfolio rebalancing completed successfully', 'success');
                await this.loadPortfolio(); // Refresh portfolio data
            } else {
                this.showNotification('Rebalance Failed', response.message || 'Unknown error', 'error');
            }
        } catch (error) {
            this.showNotification('Rebalance Error', 'Failed to rebalance portfolio', 'error');
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
            
            if (response.success) {
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
     * Initialize WebSocket connection
     */
    initializeWebSocket() {
        // Skip WebSocket initialization if not supported or endpoint not available
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
                
                // Don't try to reconnect if the endpoint doesn't exist (403/404)
                if (event.code === 1002 || event.code === 1006) {
                    console.log('🔌 WebSocket endpoint not available, disabling WebSocket');
                    this.websocket = null;
                    return;
                }
                
                this.updateConnectionStatus('disconnected');
                this.scheduleWebSocketReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('🔌 WebSocket error:', error);
                this.updateConnectionStatus('warning');
                
                // If we get an error, likely the endpoint doesn't exist
                if (this.wsReconnectAttempts === 0) {
                    console.log('🔌 WebSocket endpoint not available, disabling WebSocket');
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
        // Don't reconnect if WebSocket is disabled
        if (!this.websocket) {
            return;
        }
        
        if (this.wsReconnectAttempts < this.maxWsReconnectAttempts) {
            setTimeout(() => {
                this.wsReconnectAttempts++;
                console.log(`🔌 Attempting WebSocket reconnection (${this.wsReconnectAttempts}/${this.maxWsReconnectAttempts})`);
                this.initializeWebSocket();
            }, 5000 * this.wsReconnectAttempts); // Exponential backoff
        } else {
            console.log('🔌 Max WebSocket reconnection attempts reached, disabling WebSocket');
            this.websocket = null;
        }
    }

    /**
     * Handle visibility change (tab switching)
     */
    handleVisibilityChange() {
        if (document.hidden) {
            // Tab is hidden, reduce update frequency
            console.log('📱 Tab hidden, reducing update frequency');
        } else {
            // Tab is visible, resume normal updates
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
        
        // Log error for debugging
        const errorInfo = {
            context,
            error: error.message || error,
            timestamp: new Date(),
            stack: error.stack,
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        // In production, you might want to send this to an error tracking service
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
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        
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

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Hide loading screen and show dashboard
    setTimeout(() => {
        const loadingScreen = document.getElementById('loading-screen');
        const mainDashboard = document.getElementById('main-dashboard');
        
        if (loadingScreen) loadingScreen.style.display = 'none';
        if (mainDashboard) mainDashboard.style.display = 'block';
        
        // Initialize dashboard
        window.Dashboard.init().catch(error => {
            console.error('❌ Failed to initialize dashboard:', error);
        });
    }, 2000); // 2 second loading delay
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OdinDashboard;
}