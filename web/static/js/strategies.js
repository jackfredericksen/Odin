/**
 * Odin Bitcoin Trading Dashboard - Strategy Management
 */

class StrategyManager {
    constructor() {
        this.strategies = [];
        this.selectedStrategy = null;
        this.optimizationResults = {};
        this.backtestResults = {};
        this.apiBaseUrl = '/api/v1/strategies';
        
        // Bind methods
        this.init = this.init.bind(this);
        this.loadStrategies = this.loadStrategies.bind(this);
        this.selectStrategy = this.selectStrategy.bind(this);
        this.toggleStrategy = this.toggleStrategy.bind(this);
        this.optimizeStrategy = this.optimizeStrategy.bind(this);
        this.backtestStrategy = this.backtestStrategy.bind(this);
    }

    /**
     * Initialize strategy manager
     */
    init() {
        this.setupEventListeners();
        this.loadStrategies();
        console.log('Strategy Manager initialized');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Strategy card clicks
        document.addEventListener('click', (e) => {
            const strategyCard = e.target.closest('.strategy-card');
            if (strategyCard) {
                const strategyId = strategyCard.dataset.strategyId;
                this.selectStrategy(strategyId);
            }
        });

        // Strategy action buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="optimize"]')) {
                const strategyId = e.target.dataset.strategyId;
                this.optimizeStrategy(strategyId);
            }
            
            if (e.target.matches('[data-action="backtest"]')) {
                const strategyId = e.target.dataset.strategyId;
                this.backtestStrategy(strategyId);
            }
            
            if (e.target.matches('[data-action="toggle"]')) {
                const strategyId = e.target.dataset.strategyId;
                this.toggleStrategy(strategyId);
            }
            
            if (e.target.matches('[data-action="view-chart"]')) {
                const strategyId = e.target.dataset.strategyId;
                this.viewStrategyChart(strategyId);
            }
            
            if (e.target.matches('[data-action="configure"]')) {
                const strategyId = e.target.dataset.strategyId;
                this.configureStrategy(strategyId);
            }
        });

        // Global strategy controls
        document.getElementById('optimize-all-strategies')?.addEventListener('click', () => {
            this.optimizeAllStrategies();
        });

        document.getElementById('compare-strategies')?.addEventListener('click', () => {
            this.showStrategyComparison();
        });

        document.getElementById('export-strategies')?.addEventListener('click', () => {
            this.exportStrategiesData();
        });
    }

    /**
     * Load all strategies
     */
    async loadStrategies() {
        try {
            const response = await this.apiCall('/list');
            if (response.success) {
                this.strategies = response.data;
                this.renderStrategies();
                this.updateStrategyMetrics();
            }
        } catch (error) {
            console.error('Error loading strategies:', error);
            this.showError('Failed to load strategies');
        }
    }

    /**
     * Render strategies in the UI
     */
    renderStrategies() {
        const container = document.getElementById('strategies-grid');
        if (!container) return;

        container.innerHTML = '';

        this.strategies.forEach(strategy => {
            const card = this.createStrategyCard(strategy);
            container.appendChild(card);
        });
    }

    /**
     * Create strategy card element
     */
    createStrategyCard(strategy) {
        const card = document.createElement('div');
        card.className = `strategy-card ${strategy.active ? 'active' : ''} ${strategy.id === this.selectedStrategy?.id ? 'selected' : ''}`;
        card.dataset.strategyId = strategy.id;

        const performanceClass = this.getPerformanceClass(strategy.return);
        const riskLevel = this.calculateRiskLevel(strategy);

        card.innerHTML = `
            <div class="strategy-header">
                <div class="strategy-info">
                    <span class="strategy-name">${strategy.name}</span>
                    <span class="strategy-type">${strategy.type || 'Technical'}</span>
                </div>
                <div class="strategy-controls">
                    <span class="strategy-status ${strategy.active ? 'active' : 'inactive'}">
                        ${strategy.active ? '🟢 Active' : '⚪ Inactive'}
                    </span>
                    <button class="strategy-toggle-btn" data-action="toggle" data-strategy-id="${strategy.id}">
                        ${strategy.active ? 'Disable' : 'Enable'}
                    </button>
                </div>
            </div>

            <div class="strategy-metrics">
                <div class="metric-row">
                    <div class="metric">
                        <span class="metric-label">Total Return</span>
                        <span class="metric-value ${performanceClass}">
                            ${strategy.return >= 0 ? '+' : ''}${strategy.return.toFixed(2)}%
                        </span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Trades</span>
                        <span class="metric-value">${strategy.total_trades || 0}</span>
                    </div>
                </div>
                
                <div class="metric-row">
                    <div class="metric">
                        <span class="metric-label">Win Rate</span>
                        <span class="metric-value">${(strategy.win_rate || 0).toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Sharpe</span>
                        <span class="metric-value">${(strategy.sharpe_ratio || 0).toFixed(2)}</span>
                    </div>
                </div>
                
                <div class="metric-row">
                    <div class="metric">
                        <span class="metric-label">Max DD</span>
                        <span class="metric-value text-danger">${(strategy.max_drawdown || 0).toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Risk</span>
                        <span class="risk-indicator ${riskLevel.class}">${riskLevel.label}</span>
                    </div>
                </div>
            </div>

            <div class="strategy-actions">
                <button class="btn-secondary btn-small" data-action="view-chart" data-strategy-id="${strategy.id}">
                    📊 Chart
                </button>
                <button class="btn-secondary btn-small" data-action="optimize" data-strategy-id="${strategy.id}">
                    ⚙️ Optimize
                </button>
                <button class="btn-secondary btn-small" data-action="backtest" data-strategy-id="${strategy.id}">
                    📈 Backtest
                </button>
                <button class="btn-outline btn-small" data-action="configure" data-strategy-id="${strategy.id}">
                    ⚙️ Config
                </button>
            </div>

            <div class="strategy-performance-mini">
                <canvas id="mini-chart-${strategy.id}" width="100" height="30"></canvas>
            </div>
        `;

        // Create mini performance chart
        setTimeout(() => {
            this.createMiniChart(strategy.id, strategy.performance_history);
        }, 100);

        return card;
    }

    /**
     * Create mini performance chart
     */
    createMiniChart(strategyId, performanceData) {
        const canvas = document.getElementById(`mini-chart-${strategyId}`);
        if (!canvas || !performanceData || performanceData.length === 0) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Prepare data
        const values = performanceData.map(p => p.value || 0);
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min || 1;

        // Draw line
        ctx.strokeStyle = values[values.length - 1] >= values[0] ? '#34a853' : '#ea4335';
        ctx.lineWidth = 1.5;
        ctx.beginPath();

        values.forEach((value, index) => {
            const x = (index / (values.length - 1)) * width;
            const y = height - ((value - min) / range) * height;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();

        // Fill area
        ctx.globalAlpha = 0.1;
        ctx.fillStyle = ctx.strokeStyle;
        ctx.lineTo(width, height);
        ctx.lineTo(0, height);
        ctx.closePath();
        ctx.fill();
    }

    /**
     * Select strategy
     */
    selectStrategy(strategyId) {
        const strategy = this.strategies.find(s => s.id === strategyId);
        if (!strategy) return;

        this.selectedStrategy = strategy;
        this.updateSelectedStrategy();
        this.loadStrategyDetails(strategyId);
    }

    /**
     * Update selected strategy UI
     */
    updateSelectedStrategy() {
        // Update card selection
        document.querySelectorAll('.strategy-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        if (this.selectedStrategy) {
            const selectedCard = document.querySelector(`[data-strategy-id="${this.selectedStrategy.id}"]`);
            if (selectedCard) {
                selectedCard.classList.add('selected');
            }
        }
    }

    /**
     * Toggle strategy active status
     */
    async toggleStrategy(strategyId) {
        try {
            const strategy = this.strategies.find(s => s.id === strategyId);
            if (!strategy) return;

            const endpoint = strategy.active ? `/disable` : `/enable`;
            const response = await this.apiCall(`/${strategyId}${endpoint}`, 'POST');

            if (response.success) {
                strategy.active = !strategy.active;
                this.renderStrategies();
                
                this.showSuccess(
                    `Strategy ${strategy.active ? 'enabled' : 'disabled'}`,
                    `${strategy.name} has been ${strategy.active ? 'activated' : 'deactivated'}`
                );
            } else {
                this.showError(`Failed to ${strategy.active ? 'disable' : 'enable'} strategy`);
            }
        } catch (error) {
            console.error('Error toggling strategy:', error);
            this.showError('Failed to toggle strategy');
        }
    }

    /**
     * Optimize strategy parameters
     */
    async optimizeStrategy(strategyId) {
        try {
            const strategy = this.strategies.find(s => s.id === strategyId);
            if (!strategy) return;

            this.showLoading(`Optimizing ${strategy.name}...`);

            const response = await this.apiCall(`/${strategyId}/optimize`, 'POST', {
                optimization_method: 'grid_search',
                metric: 'sharpe_ratio',
                lookback_days: 30
            });

            this.hideLoading();

            if (response.success) {
                this.optimizationResults[strategyId] = response.data;
                this.showOptimizationResults(strategyId, response.data);
                
                this.showSuccess(
                    'Optimization Complete',
                    `${strategy.name} optimization completed successfully`
                );
            } else {
                this.showError('Optimization failed: ' + (response.message || 'Unknown error'));
            }
        } catch (error) {
            this.hideLoading();
            console.error('Error optimizing strategy:', error);
            this.showError('Failed to optimize strategy');
        }
    }

    /**
     * Backtest strategy
     */
    async backtestStrategy(strategyId, customParams = {}) {
        try {
            const strategy = this.strategies.find(s => s.id === strategyId);
            if (!strategy) return;

            this.showLoading(`Backtesting ${strategy.name}...`);

            const backtestParams = {
                start_date: customParams.start_date || this.getDefaultStartDate(),
                end_date: customParams.end_date || new Date().toISOString(),
                initial_capital: customParams.initial_capital || 10000,
                commission: customParams.commission || 0.001,
                slippage: customParams.slippage || 0.0005,
                ...customParams
            };

            const response = await this.apiCall(`/${strategyId}/backtest`, 'POST', backtestParams);

            this.hideLoading();

            if (response.success) {
                this.backtestResults[strategyId] = response.data;
                this.showBacktestResults(strategyId, response.data);
                
                this.showSuccess(
                    'Backtest Complete',
                    `${strategy.name} backtest completed successfully`
                );
            } else {
                this.showError('Backtest failed: ' + (response.message || 'Unknown error'));
            }
        } catch (error) {
            this.hideLoading();
            console.error('Error backtesting strategy:', error);
            this.showError('Failed to backtest strategy');
        }
    }

    /**
     * View strategy chart
     */
    async viewStrategyChart(strategyId) {
        try {
            const strategy = this.strategies.find(s => s.id === strategyId);
            if (!strategy) return;

            const hours = 168; // 7 days
            const response = await this.apiCall(`/${strategyId}/chart/${hours}`);

            if (response.success) {
                this.showStrategyChartModal(strategy, response.data);
            } else {
                this.showError('Failed to load strategy chart');
            }
        } catch (error) {
            console.error('Error loading strategy chart:', error);
            this.showError('Failed to load strategy chart');
        }
    }

    /**
     * Configure strategy parameters
     */
    async configureStrategy(strategyId) {
        const strategy = this.strategies.find(s => s.id === strategyId);
        if (!strategy) return;

        this.showConfigurationModal(strategy);
    }

    /**
     * Show optimization results
     */
    showOptimizationResults(strategyId, results) {
        const modal = this.createModal('optimization-results', 'Optimization Results');
        
        const content = `
            <div class="optimization-results">
                <h4>Best Parameters Found:</h4>
                <div class="parameters-grid">
                    ${Object.entries(results.best_params || {}).map(([key, value]) => `
                        <div class="parameter-item">
                            <span class="param-label">${key}:</span>
                            <span class="param-value">${value}</span>
                        </div>
                    `).join('')}
                </div>
                
                <h4>Performance Metrics:</h4>
                <div class="metrics-grid">
                    <div class="metric">
                        <span class="metric-label">Return:</span>
                        <span class="metric-value positive">${(results.return || 0).toFixed(2)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Sharpe Ratio:</span>
                        <span class="metric-value">${(results.sharpe_ratio || 0).toFixed(3)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Max Drawdown:</span>
                        <span class="metric-value negative">${(results.max_drawdown || 0).toFixed(2)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Win Rate:</span>
                        <span class="metric-value">${(results.win_rate || 0).toFixed(1)}%</span>
                    </div>
                </div>
                
                <div class="optimization-actions">
                    <button class="btn-primary" onclick="StrategyManager.applyOptimizedParams('${strategyId}')">
                        Apply Parameters
                    </button>
                    <button class="btn-secondary" onclick="StrategyManager.saveOptimizationResults('${strategyId}')">
                        Save Results
                    </button>
                </div>
            </div>
        `;
        
        modal.setContent(content);
        modal.show();
    }

    /**
     * Show backtest results
     */
    showBacktestResults(strategyId, results) {
        const modal = this.createModal('backtest-results', 'Backtest Results');
        
        const content = `
            <div class="backtest-results">
                <div class="results-summary">
                    <div class="summary-metric">
                        <span class="metric-label">Total Return:</span>
                        <span class="metric-value ${results.total_return >= 0 ? 'positive' : 'negative'}">
                            ${results.total_return >= 0 ? '+' : ''}${(results.total_return || 0).toFixed(2)}%
                        </span>
                    </div>
                    <div class="summary-metric">
                        <span class="metric-label">Annual Return:</span>
                        <span class="metric-value">${(results.annual_return || 0).toFixed(2)}%</span>
                    </div>
                    <div class="summary-metric">
                        <span class="metric-label">Sharpe Ratio:</span>
                        <span class="metric-value">${(results.sharpe_ratio || 0).toFixed(3)}</span>
                    </div>
                    <div class="summary-metric">
                        <span class="metric-label">Max Drawdown:</span>
                        <span class="metric-value negative">${(results.max_drawdown || 0).toFixed(2)}%</span>
                    </div>
                </div>
                
                <div class="backtest-chart">
                    <canvas id="backtest-chart-${strategyId}"></canvas>
                </div>
                
                <div class="trade-analysis">
                    <h4>Trade Analysis:</h4>
                    <div class="trade-stats">
                        <div class="stat">
                            <span class="stat-label">Total Trades:</span>
                            <span class="stat-value">${results.total_trades || 0}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Winning Trades:</span>
                            <span class="stat-value text-success">${results.winning_trades || 0}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Losing Trades:</span>
                            <span class="stat-value text-danger">${results.losing_trades || 0}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Average Trade:</span>
                            <span class="stat-value">${(results.avg_trade_return || 0).toFixed(3)}%</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        modal.setContent(content);
        modal.show();
        
        // Create backtest chart
        setTimeout(() => {
            this.createBacktestChart(strategyId, results.equity_curve);
        }, 100);
    }

    /**
     * Show strategy chart modal
     */
    showStrategyChartModal(strategy, chartData) {
        const modal = this.createModal('strategy-chart', `${strategy.name} - Chart Analysis`);
        
        const content = `
            <div class="strategy-chart-container">
                <div class="chart-controls">
                    <select id="chart-timeframe">
                        <option value="24">24 Hours</option>
                        <option value="168" selected>7 Days</option>
                        <option value="720">30 Days</option>
                    </select>
                    <select id="chart-indicators">
                        <option value="price">Price Only</option>
                        <option value="with-signals" selected>Price + Signals</option>
                        <option value="indicators">All Indicators</option>
                    </select>
                </div>
                <div class="strategy-chart">
                    <canvas id="strategy-detail-chart"></canvas>
                </div>
                <div class="signal-history">
                    <h4>Recent Signals:</h4>
                    <div class="signals-list" id="signals-list">
                        ${this.renderSignalsList(chartData.signals || [])}
                    </div>
                </div>
            </div>
        `;
        
        modal.setContent(content);
        modal.show();
        
        // Create detailed chart
        setTimeout(() => {
            this.createStrategyDetailChart(chartData);
        }, 100);
    }

    /**
     * Show configuration modal
     */
    showConfigurationModal(strategy) {
        const modal = this.createModal('strategy-config', `Configure ${strategy.name}`);
        
        const content = `
            <div class="strategy-configuration">
                <form id="strategy-config-form">
                    <div class="config-section">
                        <h4>Basic Settings:</h4>
                        <div class="config-grid">
                            <div class="config-item">
                                <label>Strategy Name:</label>
                                <input type="text" name="name" value="${strategy.name}" />
                            </div>
                            <div class="config-item">
                                <label>Risk Level:</label>
                                <select name="risk_level">
                                    <option value="low" ${strategy.risk_level === 'low' ? 'selected' : ''}>Low</option>
                                    <option value="medium" ${strategy.risk_level === 'medium' ? 'selected' : ''}>Medium</option>
                                    <option value="high" ${strategy.risk_level === 'high' ? 'selected' : ''}>High</option>
                                </select>
                            </div>
                            <div class="config-item">
                                <label>Position Size (%):</label>
                                <input type="number" name="position_size" value="${strategy.position_size || 10}" min="1" max="100" />
                            </div>
                            <div class="config-item">
                                <label>Stop Loss (%):</label>
                                <input type="number" name="stop_loss" value="${strategy.stop_loss || 5}" min="0.1" max="20" step="0.1" />
                            </div>
                        </div>
                    </div>
                    
                    <div class="config-section">
                        <h4>Strategy Parameters:</h4>
                        <div class="params-grid" id="strategy-params">
                            ${this.renderStrategyParams(strategy)}
                        </div>
                    </div>
                    
                    <div class="config-section">
                        <h4>Risk Management:</h4>
                        <div class="config-grid">
                            <div class="config-item">
                                <label>Max Daily Loss (%):</label>
                                <input type="number" name="max_daily_loss" value="${strategy.max_daily_loss || 3}" min="0.1" max="10" step="0.1" />
                            </div>
                            <div class="config-item">
                                <label>Max Drawdown (%):</label>
                                <input type="number" name="max_drawdown" value="${strategy.max_drawdown_limit || 15}" min="1" max="50" />
                            </div>
                            <div class="config-item checkbox-item">
                                <label>
                                    <input type="checkbox" name="enable_notifications" ${strategy.enable_notifications ? 'checked' : ''} />
                                    Enable Notifications
                                </label>
                            </div>
                            <div class="config-item checkbox-item">
                                <label>
                                    <input type="checkbox" name="auto_rebalance" ${strategy.auto_rebalance ? 'checked' : ''} />
                                    Auto Rebalance
                                </label>
                            </div>
                        </div>
                    </div>
                    
                    <div class="config-actions">
                        <button type="submit" class="btn-primary">Save Configuration</button>
                        <button type="button" class="btn-secondary" onclick="StrategyManager.resetToDefaults('${strategy.id}')">
                            Reset to Defaults
                        </button>
                        <button type="button" class="btn-outline" onclick="StrategyManager.testConfiguration('${strategy.id}')">
                            Test Configuration
                        </button>
                    </div>
                </form>
            </div>
        `;
        
        modal.setContent(content);
        modal.show();
        
        // Setup form handler
        document.getElementById('strategy-config-form').onsubmit = (e) => {
            e.preventDefault();
            this.saveStrategyConfiguration(strategy.id, new FormData(e.target));
        };
    }

    /**
     * Render strategy parameters
     */
    renderStrategyParams(strategy) {
        const params = strategy.parameters || {};
        let html = '';
        
        // Common parameters for different strategy types
        const paramConfigs = {
            'moving_average': [
                { key: 'short_period', label: 'Short Period', type: 'number', min: 1, max: 50, default: 5 },
                { key: 'long_period', label: 'Long Period', type: 'number', min: 10, max: 200, default: 20 }
            ],
            'rsi': [
                { key: 'period', label: 'RSI Period', type: 'number', min: 2, max: 50, default: 14 },
                { key: 'overbought', label: 'Overbought Level', type: 'number', min: 50, max: 90, default: 70 },
                { key: 'oversold', label: 'Oversold Level', type: 'number', min: 10, max: 50, default: 30 }
            ],
            'bollinger_bands': [
                { key: 'period', label: 'Period', type: 'number', min: 5, max: 50, default: 20 },
                { key: 'std_dev', label: 'Standard Deviation', type: 'number', min: 1, max: 4, step: 0.1, default: 2 }
            ],
            'macd': [
                { key: 'fast_period', label: 'Fast Period', type: 'number', min: 5, max: 30, default: 12 },
                { key: 'slow_period', label: 'Slow Period', type: 'number', min: 15, max: 50, default: 26 },
                { key: 'signal_period', label: 'Signal Period', type: 'number', min: 5, max: 20, default: 9 }
            ]
        };
        
        const strategyType = strategy.type?.toLowerCase() || 'moving_average';
        const configs = paramConfigs[strategyType] || paramConfigs['moving_average'];
        
        configs.forEach(config => {
            const value = params[config.key] || config.default;
            html += `
                <div class="param-item">
                    <label>${config.label}:</label>
                    <input 
                        type="${config.type}" 
                        name="param_${config.key}" 
                        value="${value}"
                        min="${config.min || ''}"
                        max="${config.max || ''}"
                        step="${config.step || ''}"
                    />
                </div>
            `;
        });
        
        return html;
    }

    /**
     * Render signals list
     */
    renderSignalsList(signals) {
        if (!signals || signals.length === 0) {
            return '<p class="no-signals">No recent signals</p>';
        }
        
        return signals.slice(0, 10).map(signal => `
            <div class="signal-item ${signal.type}">
                <div class="signal-header">
                    <span class="signal-type ${signal.type}">${signal.type.toUpperCase()}</span>
                    <span class="signal-time">${this.formatTime(signal.timestamp)}</span>
                </div>
                <div class="signal-details">
                    <span class="signal-price">${signal.price.toLocaleString()}</span>
                    <span class="signal-confidence">Confidence: ${(signal.confidence * 100).toFixed(0)}%</span>
                </div>
                ${signal.executed ? 
                    '<div class="signal-status executed">✅ Executed</div>' : 
                    '<div class="signal-status pending">⏳ Pending</div>'
                }
            </div>
        `).join('');
    }

    /**
     * Create backtest chart
     */
    createBacktestChart(strategyId, equityCurve) {
        const canvas = document.getElementById(`backtest-chart-${strategyId}`);
        if (!canvas || !equityCurve) return;

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: equityCurve.map(point => this.formatDate(point.timestamp)),
                datasets: [{
                    label: 'Portfolio Value',
                    data: equityCurve.map(point => point.value),
                    borderColor: '#1a73e8',
                    backgroundColor: '#1a73e8' + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Buy & Hold',
                    data: equityCurve.map(point => point.benchmark),
                    borderColor: '#a0aec0',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: '#a0aec0' }
                    },
                    tooltip: {
                        backgroundColor: '#1a1f2e',
                        titleColor: '#ffffff',
                        bodyColor: '#a0aec0'
                    }
                },
                scales: {
                    x: {
                        grid: { color: '#2d3748' },
                        ticks: { color: '#a0aec0' }
                    },
                    y: {
                        grid: { color: '#2d3748' },
                        ticks: { 
                            color: '#a0aec0',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Create strategy detail chart
     */
    createStrategyDetailChart(chartData) {
        const canvas = document.getElementById('strategy-detail-chart');
        if (!canvas || !chartData) return;

        const datasets = [{
            label: 'Bitcoin Price',
            data: chartData.prices.map(p => p.price),
            borderColor: '#1a73e8',
            backgroundColor: 'transparent',
            borderWidth: 2,
            yAxisID: 'y'
        }];

        // Add buy/sell signals as scatter points
        if (chartData.signals) {
            const buySignals = chartData.signals.filter(s => s.type === 'buy');
            const sellSignals = chartData.signals.filter(s => s.type === 'sell');

            if (buySignals.length > 0) {
                datasets.push({
                    label: 'Buy Signals',
                    data: buySignals.map(s => ({ x: s.timestamp, y: s.price })),
                    borderColor: '#34a853',
                    backgroundColor: '#34a853',
                    pointRadius: 8,
                    pointHoverRadius: 10,
                    showLine: false,
                    yAxisID: 'y'
                });
            }

            if (sellSignals.length > 0) {
                datasets.push({
                    label: 'Sell Signals',
                    data: sellSignals.map(s => ({ x: s.timestamp, y: s.price })),
                    borderColor: '#ea4335',
                    backgroundColor: '#ea4335',
                    pointRadius: 8,
                    pointHoverRadius: 10,
                    showLine: false,
                    yAxisID: 'y'
                });
            }
        }

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: chartData.prices.map(p => this.formatTime(p.timestamp)),
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: '#a0aec0' }
                    },
                    tooltip: {
                        backgroundColor: '#1a1f2e',
                        titleColor: '#ffffff',
                        bodyColor: '#a0aec0'
                    }
                },
                scales: {
                    x: {
                        grid: { color: '#2d3748' },
                        ticks: { color: '#a0aec0' }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: { color: '#2d3748' },
                        ticks: { 
                            color: '#a0aec0',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Calculate risk level
     */
    calculateRiskLevel(strategy) {
        const volatility = strategy.volatility || 0;
        const maxDrawdown = Math.abs(strategy.max_drawdown || 0);
        const sharpeRatio = strategy.sharpe_ratio || 0;
        
        const riskScore = (volatility * 0.4) + (maxDrawdown * 0.4) - (sharpeRatio * 0.2);
        
        if (riskScore < 5) {
            return { class: 'risk-low', label: 'Low' };
        } else if (riskScore < 15) {
            return { class: 'risk-medium', label: 'Medium' };
        } else {
            return { class: 'risk-high', label: 'High' };
        }
    }

    /**
     * Get performance class for styling
     */
    getPerformanceClass(returnValue) {
        if (returnValue >= 10) return 'performance-excellent';
        if (returnValue >= 5) return 'performance-good';
        if (returnValue >= 0) return 'performance-average';
        if (returnValue >= -5) return 'performance-poor';
        return 'performance-terrible';
    }

    /**
     * Update strategy metrics summary
     */
    updateStrategyMetrics() {
        const activeStrategies = this.strategies.filter(s => s.active).length;
        const totalReturn = this.strategies.reduce((sum, s) => sum + (s.return || 0), 0);
        const avgReturn = this.strategies.length > 0 ? totalReturn / this.strategies.length : 0;
        
        // Update summary metrics if elements exist
        const activeCountElement = document.getElementById('active-strategies-count');
        if (activeCountElement) {
            activeCountElement.textContent = activeStrategies;
        }
        
        const avgReturnElement = document.getElementById('avg-strategy-return');
        if (avgReturnElement) {
            avgReturnElement.textContent = `${avgReturn >= 0 ? '+' : ''}${avgReturn.toFixed(2)}%`;
            avgReturnElement.className = avgReturn >= 0 ? 'positive' : 'negative';
        }
    }

    /**
     * Apply optimized parameters
     */
    async applyOptimizedParams(strategyId) {
        try {
            const results = this.optimizationResults[strategyId];
            if (!results || !results.best_params) return;

            const response = await this.apiCall(`/${strategyId}/parameters/apply`, 'POST', {
                parameters: results.best_params
            });

            if (response.success) {
                this.showSuccess('Parameters Applied', 'Optimized parameters have been applied to the strategy');
                this.loadStrategies(); // Refresh strategies
            } else {
                this.showError('Failed to apply parameters');
            }
        } catch (error) {
            console.error('Error applying parameters:', error);
            this.showError('Failed to apply optimized parameters');
        }
    }

    /**
     * Save strategy configuration
     */
    async saveStrategyConfiguration(strategyId, formData) {
        try {
            const config = {};
            for (const [key, value] of formData.entries()) {
                if (key.startsWith('param_')) {
                    const paramKey = key.replace('param_', '');
                    config.parameters = config.parameters || {};
                    config.parameters[paramKey] = parseFloat(value) || value;
                } else {
                    config[key] = value;
                }
            }

            const response = await this.apiCall(`/${strategyId}/config`, 'PUT', config);

            if (response.success) {
                this.showSuccess('Configuration Saved', 'Strategy configuration updated successfully');
                this.loadStrategies(); // Refresh strategies
                this.hideAllModals();
            } else {
                this.showError('Failed to save configuration');
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showError('Failed to save strategy configuration');
        }
    }

    /**
     * Utility functions
     */
    async apiCall(endpoint, method = 'GET', data = null) {
        const url = this.apiBaseUrl + endpoint;
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        return await response.json();
    }

    createModal(id, title) {
        const existingModal = document.getElementById(id);
        if (existingModal) {
            existingModal.remove();
        }

        const modal = document.createElement('div');
        modal.id = id;
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content modal-large">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body"></div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close handlers
        modal.querySelector('.modal-close').onclick = () => modal.remove();
        modal.onclick = (e) => {
            if (e.target === modal) modal.remove();
        };

        return {
            element: modal,
            setContent: (content) => {
                modal.querySelector('.modal-body').innerHTML = content;
            },
            show: () => {
                modal.style.display = 'flex';
                modal.classList.add('show');
            },
            hide: () => {
                modal.style.display = 'none';
                modal.classList.remove('show');
            }
        };
    }

    showLoading(message) {
        // Implementation for loading indicator
    }

    hideLoading() {
        // Implementation to hide loading indicator
    }

    hideAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
            modal.classList.remove('show');
        });
    }

    showSuccess(title, message) {
        if (window.Dashboard) {
            Dashboard.showNotification(title, message, 'success');
        }
    }

    showError(message) {
        if (window.Dashboard) {
            Dashboard.showNotification('Error', message, 'error');
        }
    }

    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
    }

    formatDate(timestamp) {
        return new Date(timestamp).toLocaleDateString();
    }

    getDefaultStartDate() {
        const date = new Date();
        date.setDate(date.getDate() - 30); // 30 days ago
        return date.toISOString();
    }
}

// Create global instance
window.StrategyManager = new StrategyManager();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StrategyManager;
}