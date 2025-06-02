/**
 * Odin Bitcoin Trading Dashboard - Chart Manager
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
    }

    /**
     * Initialize all charts
     */
    init() {
        this.initPriceChart();
        this.initStrategyChart();
        this.initAllocationChart();
        
        console.log('Charts initialized');
    }

    /**
     * Initialize price chart
     */
    initPriceChart() {
        const ctx = document.getElementById('price-chart');
        if (!ctx) return;

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
                            label: (context) => {
                                return `$${context.parsed.y.toLocaleString()}`;
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
                            callback: function(value) {
                                return '$' + value.toLocaleString();
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
    }

    /**
     * Initialize strategy performance chart
     */
    initStrategyChart() {
        const ctx = document.getElementById('strategy-chart');
        if (!ctx) return;

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
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Initialize portfolio allocation chart
     */
    initAllocationChart() {
        const ctx = document.getElementById('allocation-chart');
        if (!ctx) return;

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
    }

    /**
     * Update price chart with new data
     */
    async updatePriceChart(hours = 24) {
        try {
            const response = await fetch(`/api/v1/data/history/${hours}`);
            const data = await response.json();
            
            if (data.success && this.charts.price) {
                const prices = data.data;
                const labels = prices.map(p => this.formatChartTime(p.timestamp, hours));
                const values = prices.map(p => p.price);

                this.charts.price.data.labels = labels;
                this.charts.price.data.datasets[0].data = values;
                this.charts.price.update('none');
            }
        } catch (error) {
            console.error('Error updating price chart:', error);
        }
    }

    /**
     * Update strategy performance chart
     */
    updateStrategyChart(strategies) {
        if (!this.charts.strategy) return;

        const labels = strategies.map(s => s.name);
        const returns = strategies.map(s => s.return || 0);
        const colors = returns.map(r => r >= 0 ? this.colors.success : this.colors.danger);

        this.charts.strategy.data.labels = labels;
        this.charts.strategy.data.datasets[0].data = returns;
        this.charts.strategy.data.datasets[0].backgroundColor = colors;
        this.charts.strategy.data.datasets[0].borderColor = colors;
        this.charts.strategy.update('none');
    }

    /**
     * Update portfolio allocation chart
     */
    updateAllocationChart(allocation) {
        if (!this.charts.allocation || !allocation) return;

        const labels = Object.keys(allocation);
        const values = Object.values(allocation);

        this.charts.allocation.data.labels = labels;
        this.charts.allocation.data.datasets[0].data = values;
        this.charts.allocation.update('none');
    }

    /**
     * Create candlestick chart for detailed analysis
     */
    createCandlestickChart(containerId, data) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'candlestick',
            data: {
                datasets: [{
                    label: 'Bitcoin Price',
                    data: data.map(candle => ({
                        x: candle.timestamp,
                        o: candle.open,
                        h: candle.high,
                        l: candle.low,
                        c: candle.close
                    })),
                    borderColor: this.colors.primary,
                    backgroundColor: this.colors.primary + '20'
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    x: {
                        ...this.defaultOptions.scales.x,
                        type: 'time',
                        time: {
                            unit: 'hour'
                        }
                    },
                    y: {
                        ...this.defaultOptions.scales.y,
                        ticks: {
                            ...this.defaultOptions.scales.y.ticks,
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
     * Create volume chart
     */
    createVolumeChart(containerId, data) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => this.formatChartTime(d.timestamp)),
                datasets: [{
                    label: 'Volume',
                    data: data.map(d => d.volume),
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
                                return `Volume: ${context.parsed.y.toLocaleString()} BTC`;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Create performance comparison chart
     */
    createPerformanceChart(containerId, strategies) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return null;

        const datasets = strategies.map((strategy, index) => ({
            label: strategy.name,
            data: strategy.performance_history || [],
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
                            callback: function(value) {
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
    }

    /**
     * Create risk metrics radar chart
     */
    createRiskChart(containerId, riskData) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Volatility', 'Sharpe Ratio', 'Max Drawdown', 'Win Rate', 'Profit Factor', 'Sortino Ratio'],
                datasets: [{
                    label: 'Current Portfolio',
                    data: [
                        riskData.volatility || 0,
                        riskData.sharpe_ratio || 0,
                        Math.abs(riskData.max_drawdown || 0),
                        riskData.win_rate || 0,
                        riskData.profit_factor || 0,
                        riskData.sortino_ratio || 0
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
    }

    /**
     * Create correlation matrix heatmap
     */
    createCorrelationChart(containerId, correlationData) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return null;

        // This would typically use a specialized heatmap library
        // For now, we'll create a simple representation
        const labels = Object.keys(correlationData);
        
        return new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: labels.map((label, i) => ({
                    label: label,
                    data: labels.map((otherLabel, j) => ({
                        x: i,
                        y: j,
                        v: correlationData[label][otherLabel] || 0
                    })),
                    backgroundColor: function(context) {
                        const value = context.parsed.v;
                        const alpha = Math.abs(value);
                        return value >= 0 ? `rgba(52, 168, 83, ${alpha})` : `rgba(234, 67, 53, ${alpha})`;
                    },
                    pointRadius: 15
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1a1f2e',
                        titleColor: '#ffffff',
                        bodyColor: '#a0aec0',
                        borderColor: '#2d3748',
                        borderWidth: 1,
                        callbacks: {
                            title: () => 'Correlation',
                            label: (context) => {
                                return `${context.dataset.label}: ${context.parsed.v.toFixed(3)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        ticks: {
                            stepSize: 1,
                            callback: function(value) {
                                return labels[value] || '';
                            },
                            color: '#a0aec0'
                        },
                        grid: {
                            color: '#2d3748'
                        }
                    },
                    y: {
                        ticks: {
                            stepSize: 1,
                            callback: function(value) {
                                return labels[value] || '';
                            },
                            color: '#a0aec0'
                        },
                        grid: {
                            color: '#2d3748'
                        }
                    }
                }
            }
        });
    }

    /**
     * Format time for chart labels
     */
    formatChartTime(timestamp, hours = 24) {
        const date = new Date(timestamp);
        
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
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = {};
    }

    /**
     * Resize all charts
     */
    resize() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.resize();
            }
        });
    }

    /**
     * Export chart as image
     */
    exportChart(chartKey, filename = 'chart.png') {
        const chart = this.charts[chartKey];
        if (chart) {
            const url = chart.toBase64Image();
            const link = document.createElement('a');
            link.download = filename;
            link.href = url;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
}

// Create global instance
window.ChartManager = new ChartManager();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartManager;
}