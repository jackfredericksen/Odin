/**
 * Odin Bitcoin Trading Dashboard - Chart Manager (Updated with Real Data Integration)
 */

class ChartManager {
    constructor() {
        this.charts = {};
        this.colors = {
            primary: '#1a73e8',
            success: '#34a853',
            danger: '#ea4335',
            warning: '#fbbc04',
            purple: '#9c27b0',
            orange: '#ff9800',
            cyan: '#00bcd4',
            brown: '#795548'
        };
        
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#a0aec0',
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#1a1f2e',
                    titleColor: '#ffffff',
                    bodyColor: '#a0aec0',
                    borderColor: '#2d3748',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#2d3748',
                        borderColor: '#4a5568'
                    },
                    ticks: {
                        color: '#a0aec0'
                    }
                },
                y: {
                    grid: {
                        color: '#2d3748',
                        borderColor: '#4a5568'
                    },
                    ticks: {
                        color: '#a0aec0'
                    }
                }
            }
        };

        // Chart update flags to prevent excessive updates
        this.updateFlags = {
            price: false,
            strategy: false,
            allocation: false
        };
    }

    /**
     * Initialize all charts
     */
    init() {
        try {
            this.initPriceChart();
            this.initStrategyChart();
            this.initAllocationChart();
            
            console.log('Chart Manager initialized successfully');
        } catch (error) {
            console.error('Error initializing charts:', error);
        }
    }

    /**
     * Initialize price chart
     */
    initPriceChart() {
        const ctx = document.getElementById('price-chart');
        if (!ctx) {
            console.warn('Price chart canvas not found');
            return;
        }

        this.charts.price = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Bitcoin Price',
                    data: [],
                    borderColor: this.colors.primary,
                    backgroundColor: this.colors.primary + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6
                }]
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        ...this.defaultOptions.plugins.tooltip,
                        callbacks: {
                            title: (context) => {
                                return this.formatTooltipTime(context[0].label);
                            },
                            label: (context) => {
                                return `Price: ${this.formatCurrency(context.parsed.y)}`;
                            }
                        }
                    }
                },
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        ticks: {
                            ...this.defaultOptions.scales.y.ticks,
                            callback: (value) => {
                                return this.formatCurrency(value);
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });

        console.log('Price chart initialized');
    }

    /**
     * Initialize strategy performance chart
     */
    initStrategyChart() {
        const ctx = document.getElementById('strategy-chart');
        if (!ctx) {
            console.warn('Strategy chart canvas not found');
            return;
        }

        this.charts.strategy = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Returns (%)',
                    data: [],
                    backgroundColor: [],
                    borderColor: [],
                    borderWidth: 1
                }]
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        ...this.defaultOptions.plugins.tooltip,
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.y;
                                return `${context.dataset.label}: ${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
                            }
                        }
                    }
                },
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        ticks: {
                            ...this.defaultOptions.scales.y.ticks,
                            callback: (value) => {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });

        console.log('Strategy chart initialized');
    }

    /**
     * Initialize portfolio allocation chart
     */
    initAllocationChart() {
        const ctx = document.getElementById('allocation-chart');
        if (!ctx) {
            console.warn('Allocation chart canvas not found');
            return;
        }

        this.charts.allocation = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        this.colors.primary,
                        this.colors.success,
                        this.colors.warning,
                        this.colors.purple,
                        this.colors.orange,
                        this.colors.cyan
                    ],
                    borderWidth: 2,
                    borderColor: '#0f1419'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#a0aec0',
                            font: {
                                size: 11
                            },
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1a1f2e',
                        titleColor: '#ffffff',
                        bodyColor: '#a0aec0',
                        borderColor: '#2d3748',
                        borderWidth: 1,
                        callbacks: {
                            label: (context) => {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${percentage}%`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });

        console.log('Allocation chart initialized');
    }

    /**
     * Update price chart with new data
     */
    async updatePriceChart(hours = 24) {
        if (this.updateFlags.price) {
            console.log('Price chart update already in progress');
            return;
        }

        this.updateFlags.price = true;

        try {
            console.log(`Updating price chart for ${hours} hours`);
            
            const response = await fetch(`/api/v1/data/history/${hours}`);
            const data = await response.json();
            
            if (data.success && data.data && this.charts.price) {
                const prices = data.data;
                
                if (prices.length === 0) {
                    console.warn('No price data received');
                    return;
                }

                const labels = prices.map(p => this.formatChartTime(p.timestamp, hours));
                const values = prices.map(p => p.price);

                this.charts.price.data.labels = labels;
                this.charts.price.data.datasets[0].data = values;
                
                // Update chart title based on timeframe
                this.charts.price.options.plugins.title = {
                    display: true,
                    text: `Bitcoin Price - Last ${hours} Hours`,
                    color: '#ffffff'
                };

                this.charts.price.update('none');
                console.log(`Price chart updated with ${prices.length} data points`);
            } else {
                console.error('Failed to update price chart:', data.error || 'No data');
                
                // Show placeholder data if no real data
                if (this.charts.price) {
                    this.charts.price.data.labels = ['No Data'];
                    this.charts.price.data.datasets[0].data = [0];
                    this.charts.price.update('none');
                }
            }
        } catch (error) {
            console.error('Error updating price chart:', error);
            
            // Show error state in chart
            if (this.charts.price) {
                this.charts.price.data.labels = ['Error'];
                this.charts.price.data.datasets[0].data = [0];
                this.charts.price.update('none');
            }
        } finally {
            this.updateFlags.price = false;
        }
    }

    /**
     * Update strategy performance chart
     */
    updateStrategyChart(strategies) {
        if (!this.charts.strategy || this.updateFlags.strategy) {
            return;
        }

        this.updateFlags.strategy = true;

        try {
            if (!strategies || strategies.length === 0) {
                // Clear chart if no strategies
                this.charts.strategy.data.labels = ['No Strategies'];
                this.charts.strategy.data.datasets[0].data = [0];
                this.charts.strategy.data.datasets[0].backgroundColor = [this.colors.primary + '40'];
                this.charts.strategy.data.datasets[0].borderColor = [this.colors.primary];
                this.charts.strategy.update('none');
                return;
            }

            const labels = strategies.map(s => s.name || s.id);
            const returns = strategies.map(s => s.return || 0);
            const colors = returns.map(r => r >= 0 ? this.colors.success : this.colors.danger);

            this.charts.strategy.data.labels = labels;
            this.charts.strategy.data.datasets[0].data = returns;
            this.charts.strategy.data.datasets[0].backgroundColor = colors;
            this.charts.strategy.data.datasets[0].borderColor = colors;
            
            this.charts.strategy.update('none');
            console.log(`Strategy chart updated with ${strategies.length} strategies`);
        } catch (error) {
            console.error('Error updating strategy chart:', error);
        } finally {
            this.updateFlags.strategy = false;
        }
    }

    /**
     * Update portfolio allocation chart
     */
    updateAllocationChart(allocation) {
        if (!this.charts.allocation || !allocation || this.updateFlags.allocation) {
            return;
        }

        this.updateFlags.allocation = true;

        try {
            const labels = Object.keys(allocation);
            const values = Object.values(allocation);

            if (labels.length === 0) {
                // Show default allocation if no data
                this.charts.allocation.data.labels = ['No Data'];
                this.charts.allocation.data.datasets[0].data = [100];
                this.charts.allocation.update('none');
                return;
            }

            this.charts.allocation.data.labels = labels;
            this.charts.allocation.data.datasets[0].data = values;
            this.charts.allocation.update('none');
            
            console.log(`Allocation chart updated with ${labels.length} allocations`);
        } catch (error) {
            console.error('Error updating allocation chart:', error);
        } finally {
            this.updateFlags.allocation = false;
        }
    }

    /**
     * Create performance comparison chart
     */
    createPerformanceChart(containerId, strategies) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return null;

        try {
            const datasets = strategies.map((strategy, index) => ({
                label: strategy.name,
                data: strategy.performance_history || this.generateMockPerformanceData(30),
                borderColor: Object.values(this.colors)[index % Object.keys(this.colors).length],
                backgroundColor: Object.values(this.colors)[index % Object.keys(this.colors).length] + '20',
                borderWidth: 2,
                fill: false,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 4
            }));

            return new Chart(ctx, {
                type: 'line',
                data: {
                    labels: this.generateTimeLabels(30), // 30 days
                    datasets: datasets
                },
                options: {
                    ...this.defaultOptions,
                    plugins: {
                        ...this.defaultOptions.plugins,
                        tooltip: {
                            ...this.defaultOptions.plugins.tooltip,
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                label: (context) => {
                                    const value = context.parsed.y;
                                    return `${context.dataset.label}: ${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        ...this.defaultOptions.scales,
                        y: {
                            ...this.defaultOptions.scales.y,
                            ticks: {
                                ...this.defaultOptions.scales.y.ticks,
                                callback: (value) => {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    interaction: {
                        mode: 'index',
                        intersect: false
                    }
                }
            });
        } catch (error) {
            console.error('Error creating performance chart:', error);
            return null;
        }
    }

    /**
     * Create volume chart
     */
    createVolumeChart(containerId, data) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return null;

        try {
            return new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(d => this.formatChartTime(d.timestamp)),
                    datasets: [{
                        label: 'Volume',
                        data: data.map(d => d.volume || 0),
                        backgroundColor: this.colors.primary + '40',
                        borderColor: this.colors.primary,
                        borderWidth: 1
                    }]
                },
                options: {
                    ...this.defaultOptions,
                    plugins: {
                        ...this.defaultOptions.plugins,
                        tooltip: {
                            ...this.defaultOptions.plugins.tooltip,
                            callbacks: {
                                label: (context) => {
                                    return `Volume: ${this.formatNumber(context.parsed.y)} BTC`;
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating volume chart:', error);
            return null;
        }
    }

    /**
     * Create risk metrics radar chart
     */
    createRiskChart(containerId, riskData) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return null;

        try {
            return new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: ['Volatility', 'Sharpe Ratio', 'Max Drawdown', 'Win Rate', 'Profit Factor', 'Sortino Ratio'],
                    datasets: [{
                        label: 'Current Portfolio',
                        data: [
                            Math.min(riskData.volatility || 0, 100),
                            Math.max(Math.min((riskData.sharpe_ratio || 0) * 20, 100), 0),
                            Math.min(Math.abs(riskData.max_drawdown || 0), 100),
                            Math.min(riskData.win_rate || 0, 100),
                            Math.max(Math.min((riskData.profit_factor || 0) * 50, 100), 0),
                            Math.max(Math.min((riskData.sortino_ratio || 0) * 20, 100), 0)
                        ],
                        backgroundColor: this.colors.primary + '20',
                        borderColor: this.colors.primary,
                        borderWidth: 2,
                        pointBackgroundColor: this.colors.primary,
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: this.colors.primary
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: '#a0aec0',
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            backgroundColor: '#1a1f2e',
                            titleColor: '#ffffff',
                            bodyColor: '#a0aec0',
                            borderColor: '#2d3748',
                            borderWidth: 1
                        }
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100,
                            grid: {
                                color: '#2d3748'
                            },
                            angleLines: {
                                color: '#2d3748'
                            },
                            pointLabels: {
                                color: '#a0aec0',
                                font: {
                                    size: 11
                                }
                            },
                            ticks: {
                                color: '#a0aec0',
                                font: {
                                    size: 10
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating risk chart:', error);
            return null;
        }
    }

    /**
     * Create candlestick chart for detailed analysis
     */
    createCandlestickChart(containerId, data) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return null;

        try {
            // Since Chart.js doesn't have native candlestick support,
            // we'll create a line chart with high/low ranges
            return new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(candle => this.formatChartTime(candle.timestamp)),
                    datasets: [
                        {
                            label: 'High',
                            data: data.map(candle => candle.high || candle.close),
                            borderColor: this.colors.success,
                            backgroundColor: 'transparent',
                            borderWidth: 1,
                            pointRadius: 0
                        },
                        {
                            label: 'Close',
                            data: data.map(candle => candle.close),
                            borderColor: this.colors.primary,
                            backgroundColor: this.colors.primary + '20',
                            borderWidth: 2,
                            fill: false,
                            pointRadius: 0
                        },
                        {
                            label: 'Low',
                            data: data.map(candle => candle.low || candle.close),
                            borderColor: this.colors.danger,
                            backgroundColor: 'transparent',
                            borderWidth: 1,
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    ...this.defaultOptions,
                    scales: {
                        ...this.defaultOptions.scales,
                        y: {
                            ...this.defaultOptions.scales.y,
                            ticks: {
                                ...this.defaultOptions.scales.y.ticks,
                                callback: (value) => {
                                    return this.formatCurrency(value);
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating candlestick chart:', error);
            return null;
        }
    }

    /**
     * Format time for chart labels based on timeframe
     */
    formatChartTime(timestamp, hours = 24) {
        try {
            const date = new Date(timestamp);
            
            if (isNaN(date.getTime())) {
                return 'Invalid';
            }
            
            if (hours <= 24) {
                return date.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } else if (hours <= 168) { // 7 days
                return date.toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit'
                });
            } else {
                return date.toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric'
                });
            }
        } catch (error) {
            console.error('Error formatting chart time:', error);
            return 'Error';
        }
    }

    /**
     * Format time for tooltips
     */
    formatTooltipTime(label) {
        try {
            return label;
        } catch (error) {
            return 'Unknown Time';
        }
    }

    /**
     * Format currency values
     */
    formatCurrency(value) {
        if (typeof value !== 'number' || isNaN(value)) {
            return '$0.00';
        }
        
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }

    /**
     * Format numbers with appropriate units
     */
    formatNumber(value, decimals = 2) {
        if (typeof value !== 'number' || isNaN(value)) {
            return '0';
        }

        if (value >= 1000000) {
            return (value / 1000000).toFixed(decimals) + 'M';
        } else if (value >= 1000) {
            return (value / 1000).toFixed(decimals) + 'K';
        } else {
            return value.toFixed(decimals);
        }
    }

    /**
     * Generate time labels for charts
     */
    generateTimeLabels(days) {
        const labels = [];
        const now = new Date();
        
        for (let i = days; i >= 0; i--) {
            const date = new Date(now.getTime() - (i * 24 * 60 * 60 * 1000));
            labels.push(date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric'
            }));
        }
        
        return labels;
    }

    /**
     * Generate mock performance data for testing
     */
    generateMockPerformanceData(days) {
        const data = [];
        let value = 0;
        
        for (let i = 0; i < days; i++) {
            value += (Math.random() - 0.5) * 2; // Random walk
            data.push(value);
        }
        
        return data;
    }

    /**
     * Update chart theme (for dark/light mode toggle)
     */
    updateTheme(isDark = true) {
        const textColor = isDark ? '#a0aec0' : '#2d3748';
        const gridColor = isDark ? '#2d3748' : '#e2e8f0';
        
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.options) {
                // Update text colors
                if (chart.options.plugins?.legend?.labels) {
                    chart.options.plugins.legend.labels.color = textColor;
                }
                
                // Update scale colors
                if (chart.options.scales) {
                    Object.keys(chart.options.scales).forEach(scaleKey => {
                        const scale = chart.options.scales[scaleKey];
                        if (scale.ticks) scale.ticks.color = textColor;
                        if (scale.grid) scale.grid.color = gridColor;
                    });
                }
                
                chart.update('none');
            }
        });
    }

    /**
     * Destroy all charts
     */
    destroy() {
        Object.keys(this.charts).forEach(chartKey => {
            if (this.charts[chartKey]) {
                try {
                    this.charts[chartKey].destroy();
                } catch (error) {
                    console.error(`Error destroying chart ${chartKey}:`, error);
                }
            }
        });
        this.charts = {};
        console.log('All charts destroyed');
    }

    /**
     * Resize all charts
     */
    resize() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                try {
                    chart.resize();
                } catch (error) {
                    console.error('Error resizing chart:', error);
                }
            }
        });
    }

    /**
     * Export chart as image
     */
    exportChart(chartKey, filename = 'chart.png') {
        const chart = this.charts[chartKey];
        if (chart) {
            try {
                const url = chart.toBase64Image();
                const link = document.createElement('a');
                link.download = filename;
                link.href = url;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                console.log(`Chart ${chartKey} exported as ${filename}`);
            } catch (error) {
                console.error(`Error exporting chart ${chartKey}:`, error);
            }
        }
    }

    /**
     * Get chart statistics
     */
    getChartStats() {
        const stats = {};
        
        Object.keys(this.charts).forEach(chartKey => {
            const chart = this.charts[chartKey];
            if (chart && chart.data) {
                stats[chartKey] = {
                    type: chart.config.type,
                    datasets: chart.data.datasets.length,
                    dataPoints: chart.data.datasets.reduce((total, dataset) => {
                        return total + (dataset.data ? dataset.data.length : 0);
                    }, 0),
                    labels: chart.data.labels ? chart.data.labels.length : 0
                };
            }
        });
        
        return stats;
    }

    /**
     * Check if all required charts are loaded
     */
    areChartsLoaded() {
        const requiredCharts = ['price', 'strategy', 'allocation'];
        return requiredCharts.every(chartKey => this.charts[chartKey] !== undefined);
    }

    /**
     * Refresh all charts
     */
    async refreshAllCharts() {
        try {
            console.log('Refreshing all charts...');
            
            // Refresh price chart
            await this.updatePriceChart();
            
            // Refresh other charts by fetching fresh data
            const dashboard = window.Dashboard;
            if (dashboard) {
                await dashboard.loadStrategies();
                await dashboard.loadPortfolio();
            }
            
            console.log('All charts refreshed');
        } catch (error) {
            console.error('Error refreshing charts:', error);
        }
    }

    /**
     * Add chart animation on data update
     */
    animateChart(chartKey, animationType = 'bounce') {
        const chart = this.charts[chartKey];
        if (chart) {
            chart.update(animationType);
        }
    }

    /**
     * Set chart loading state
     */
    setChartLoading(chartKey, isLoading = true) {
        const chart = this.charts[chartKey];
        const canvas = document.getElementById(chartKey + '-chart');
        
        if (canvas) {
            const container = canvas.parentElement;
            if (isLoading) {
                container.classList.add('loading');
            } else {
                container.classList.remove('loading');
            }
        }
    }

    /**
     * Health check for chart manager
     */
    healthCheck() {
        const health = {
            chartsLoaded: Object.keys(this.charts).length,
            requiredCharts: this.areChartsLoaded(),
            updateFlags: this.updateFlags,
            errors: []
        };

        // Check for chart errors
        Object.keys(this.charts).forEach(chartKey => {
            const chart = this.charts[chartKey];
            if (!chart) {
                health.errors.push(`Chart ${chartKey} not initialized`);
            }
        });

        return health;
    }
}

// Create global instance
window.ChartManager = new ChartManager();

// Handle window resize
window.addEventListener('resize', () => {
    if (window.ChartManager) {
        window.ChartManager.resize();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartManager;
}

