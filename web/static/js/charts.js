/**
 * Odin Bitcoin Trading Dashboard - Chart Manager (FIXED VERSION)
 */

class ChartManager {
    constructor() {
        this.charts = {};
        this.colors = {
            primary: "#1a73e8",
            success: "#34a853",
            danger: "#ea4335",
            warning: "#fbbc04",
            purple: "#9c27b0",
            orange: "#ff9800",
            cyan: "#00bcd4",
            brown: "#795548",
        };

        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: "top",
                    labels: {
                        color: "#a0aec0",
                        font: {
                            size: 12,
                        },
                    },
                },
                tooltip: {
                    backgroundColor: "#1a1f2e",
                    titleColor: "#ffffff",
                    bodyColor: "#a0aec0",
                    borderColor: "#2d3748",
                    borderWidth: 1,
                },
            },
            scales: {
                x: {
                    grid: {
                        color: "#2d3748",
                        borderColor: "#4a5568",
                    },
                    ticks: {
                        color: "#a0aec0",
                    },
                },
                y: {
                    grid: {
                        color: "#2d3748",
                        borderColor: "#4a5568",
                    },
                    ticks: {
                        color: "#a0aec0",
                    },
                },
            },
        };

        // Chart update flags to prevent excessive updates
        this.updateFlags = {
            price: false,
            strategy: false,
            allocation: false,
        };

        // FIXED: Add initialization state tracking
        this.isInitialized = false;
    }

    /**
     * FIXED: Initialize all charts with proper error handling
     */
    init() {
        try {
            console.log("📊 Initializing Chart Manager...");

            // FIXED: Check if Chart.js is available
            if (typeof Chart === "undefined") {
                console.error("❌ Chart.js is not loaded");
                return false;
            }

            this.initPriceChart();
            this.initStrategyChart();
            this.initAllocationChart();

            this.isInitialized = true;
            console.log("✅ Chart Manager initialized successfully");
            return true;
        } catch (error) {
            console.error("❌ Error initializing charts:", error);
            return false;
        }
    }

    /**
     * FIXED: Initialize price chart with better error handling
     */
    initPriceChart() {
        const ctx = document.getElementById("price-chart");
        if (!ctx) {
            console.warn("⚠️ Price chart canvas not found");
            return;
        }

        try {
            // FIXED: Destroy existing chart if it exists
            if (this.charts.price) {
                this.charts.price.destroy();
            }

            this.charts.price = new Chart(ctx, {
                type: "line",
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: "Bitcoin Price",
                            data: [],
                            borderColor: this.colors.primary,
                            backgroundColor: this.colors.primary + "20",
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 0,
                            pointHoverRadius: 6,
                        },
                    ],
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
                                },
                            },
                        },
                    },
                    scales: {
                        ...this.defaultOptions.scales,
                        y: {
                            ...this.defaultOptions.scales.y,
                            ticks: {
                                ...this.defaultOptions.scales.y.ticks,
                                callback: (value) => {
                                    return this.formatCurrency(value);
                                },
                            },
                        },
                    },
                    interaction: {
                        intersect: false,
                        mode: "index",
                    },
                },
            });

            console.log("✅ Price chart initialized");
        } catch (error) {
            console.error("❌ Error initializing price chart:", error);
        }
    }

    /**
     * FIXED: Initialize strategy performance chart with better error handling
     */
    initStrategyChart() {
        const ctx = document.getElementById("strategy-chart");
        if (!ctx) {
            console.warn("⚠️ Strategy chart canvas not found");
            return;
        }

        try {
            // FIXED: Destroy existing chart if it exists
            if (this.charts.strategy) {
                this.charts.strategy.destroy();
            }

            this.charts.strategy = new Chart(ctx, {
                type: "bar",
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: "Returns (%)",
                            data: [],
                            backgroundColor: [],
                            borderColor: [],
                            borderWidth: 1,
                        },
                    ],
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
                                    return `${context.dataset.label}: ${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
                                },
                            },
                        },
                    },
                    scales: {
                        ...this.defaultOptions.scales,
                        y: {
                            ...this.defaultOptions.scales.y,
                            ticks: {
                                ...this.defaultOptions.scales.y.ticks,
                                callback: (value) => {
                                    return value + "%";
                                },
                            },
                        },
                    },
                },
            });

            console.log("✅ Strategy chart initialized");
        } catch (error) {
            console.error("❌ Error initializing strategy chart:", error);
        }
    }

    /**
     * FIXED: Initialize portfolio allocation chart with better error handling
     */
    initAllocationChart() {
        const ctx = document.getElementById("allocation-chart");
        if (!ctx) {
            console.warn("⚠️ Allocation chart canvas not found");
            return;
        }

        try {
            // FIXED: Destroy existing chart if it exists
            if (this.charts.allocation) {
                this.charts.allocation.destroy();
            }

            this.charts.allocation = new Chart(ctx, {
                type: "doughnut",
                data: {
                    labels: [],
                    datasets: [
                        {
                            data: [],
                            backgroundColor: [
                                this.colors.primary,
                                this.colors.success,
                                this.colors.warning,
                                this.colors.purple,
                                this.colors.orange,
                                this.colors.cyan,
                            ],
                            borderWidth: 2,
                            borderColor: "#0f1419",
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: {
                                color: "#a0aec0",
                                font: {
                                    size: 11,
                                },
                                padding: 15,
                            },
                        },
                        tooltip: {
                            backgroundColor: "#1a1f2e",
                            titleColor: "#ffffff",
                            bodyColor: "#a0aec0",
                            borderColor: "#2d3748",
                            borderWidth: 1,
                            callbacks: {
                                label: (context) => {
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage =
                                        total > 0
                                            ? ((context.parsed / total) * 100).toFixed(1)
                                            : "0.0";
                                    return `${context.label}: ${percentage}%`;
                                },
                            },
                        },
                    },
                    cutout: "60%",
                },
            });

            console.log("✅ Allocation chart initialized");
        } catch (error) {
            console.error("❌ Error initializing allocation chart:", error);
        }
    }

    /**
     * FIXED: Update price chart with new data and proper API integration
     */
    async updatePriceChart(hours = 24) {
        if (this.updateFlags.price) {
            console.log("⚠️ Price chart update already in progress");
            return;
        }

        if (!this.charts.price) {
            console.warn("⚠️ Price chart not initialized");
            return;
        }

        this.updateFlags.price = true;

        try {
            console.log(`📊 Updating price chart for ${hours} hours`);

            const response = await fetch(`/api/v1/data/history/${hours}`);
            const data = await response.json();

            if (data.success && data.data && Array.isArray(data.data)) {
                const prices = data.data;

                if (prices.length === 0) {
                    console.warn("⚠️ No price data received");
                    this.showEmptyChart("price");
                    return;
                }

                const labels = prices.map((p) => this.formatChartTime(p.timestamp, hours));
                const values = prices.map((p) => p.price);

                this.charts.price.data.labels = labels;
                this.charts.price.data.datasets[0].data = values;

                // Update chart title based on timeframe
                this.charts.price.options.plugins.title = {
                    display: true,
                    text: `Bitcoin Price - Last ${hours} Hours`,
                    color: "#ffffff",
                };

                this.charts.price.update("none");
                console.log(`✅ Price chart updated with ${prices.length} data points`);
            } else {
                console.error(
                    "❌ Failed to update price chart:",
                    data.error || "Invalid data format",
                );
                this.showEmptyChart("price");
            }
        } catch (error) {
            console.error("❌ Error updating price chart:", error);
            this.showErrorChart("price");
        } finally {
            this.updateFlags.price = false;
        }
    }

    /**
     * FIXED: Update strategy performance chart with better data handling
     */
    updateStrategyChart(strategies) {
        if (!this.charts.strategy || this.updateFlags.strategy) {
            return;
        }

        this.updateFlags.strategy = true;

        try {
            if (!strategies || !Array.isArray(strategies) || strategies.length === 0) {
                this.showEmptyChart("strategy");
                return;
            }

            const labels = strategies.map((s) => s.name || s.id || "Unknown");
            const returns = strategies.map((s) => s.return || 0);
            const colors = returns.map((r) => (r >= 0 ? this.colors.success : this.colors.danger));

            this.charts.strategy.data.labels = labels;
            this.charts.strategy.data.datasets[0].data = returns;
            this.charts.strategy.data.datasets[0].backgroundColor = colors;
            this.charts.strategy.data.datasets[0].borderColor = colors;

            this.charts.strategy.update("none");
            console.log(`✅ Strategy chart updated with ${strategies.length} strategies`);
        } catch (error) {
            console.error("❌ Error updating strategy chart:", error);
            this.showErrorChart("strategy");
        } finally {
            this.updateFlags.strategy = false;
        }
    }

    /**
     * FIXED: Update portfolio allocation chart with better data handling
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
                this.showEmptyChart("allocation");
                return;
            }

            // FIXED: Ensure values are numbers
            const numericValues = values.map((v) =>
                typeof v === "number" ? v : parseFloat(v) || 0,
            );

            this.charts.allocation.data.labels = labels;
            this.charts.allocation.data.datasets[0].data = numericValues;
            this.charts.allocation.update("none");

            console.log(`✅ Allocation chart updated with ${labels.length} allocations`);
        } catch (error) {
            console.error("❌ Error updating allocation chart:", error);
            this.showErrorChart("allocation");
        } finally {
            this.updateFlags.allocation = false;
        }
    }

    /**
     * FIXED: Show empty state for charts
     */
    showEmptyChart(chartType) {
        const chart = this.charts[chartType];
        if (!chart) return;

        try {
            switch (chartType) {
                case "price":
                    chart.data.labels = ["No Data Available"];
                    chart.data.datasets[0].data = [0];
                    break;
                case "strategy":
                    chart.data.labels = ["No Strategies"];
                    chart.data.datasets[0].data = [0];
                    chart.data.datasets[0].backgroundColor = [this.colors.primary + "40"];
                    chart.data.datasets[0].borderColor = [this.colors.primary];
                    break;
                case "allocation":
                    chart.data.labels = ["No Data"];
                    chart.data.datasets[0].data = [100];
                    break;
            }
            chart.update("none");
        } catch (error) {
            console.error(`❌ Error showing empty chart for ${chartType}:`, error);
        }
    }

    /**
     * FIXED: Show error state for charts
     */
    showErrorChart(chartType) {
        const chart = this.charts[chartType];
        if (!chart) return;

        try {
            switch (chartType) {
                case "price":
                    chart.data.labels = ["Error Loading Data"];
                    chart.data.datasets[0].data = [0];
                    break;
                case "strategy":
                    chart.data.labels = ["Error"];
                    chart.data.datasets[0].data = [0];
                    chart.data.datasets[0].backgroundColor = [this.colors.danger + "40"];
                    chart.data.datasets[0].borderColor = [this.colors.danger];
                    break;
                case "allocation":
                    chart.data.labels = ["Error"];
                    chart.data.datasets[0].data = [100];
                    break;
            }
            chart.update("none");
        } catch (error) {
            console.error(`❌ Error showing error chart for ${chartType}:`, error);
        }
    }

    /**
     * FIXED: Format time for chart labels based on timeframe
     */
    formatChartTime(timestamp, hours = 24) {
        try {
            const date = new Date(timestamp);

            if (isNaN(date.getTime())) {
                return "Invalid";
            }

            if (hours <= 24) {
                return date.toLocaleTimeString("en-US", {
                    hour: "2-digit",
                    minute: "2-digit",
                });
            } else if (hours <= 168) {
                // 7 days
                return date.toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                });
            } else {
                return date.toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                });
            }
        } catch (error) {
            console.error("❌ Error formatting chart time:", error);
            return "Error";
        }
    }

    /**
     * Format time for tooltips
     */
    formatTooltipTime(label) {
        try {
            return label;
        } catch (error) {
            return "Unknown Time";
        }
    }

    /**
     * Format currency values
     */
    formatCurrency(value) {
        if (typeof value !== "number" || isNaN(value)) {
            return "$0.00";
        }

        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(value);
    }

    /**
     * Format numbers with appropriate units
     */
    formatNumber(value, decimals = 2) {
        if (typeof value !== "number" || isNaN(value)) {
            return "0";
        }

        if (value >= 1000000) {
            return (value / 1000000).toFixed(decimals) + "M";
        } else if (value >= 1000) {
            return (value / 1000).toFixed(decimals) + "K";
        } else {
            return value.toFixed(decimals);
        }
    }

    /**
     * FIXED: Destroy all charts safely
     */
    destroy() {
        Object.keys(this.charts).forEach((chartKey) => {
            if (this.charts[chartKey]) {
                try {
                    this.charts[chartKey].destroy();
                    console.log(`✅ Chart ${chartKey} destroyed`);
                } catch (error) {
                    console.error(`❌ Error destroying chart ${chartKey}:`, error);
                }
            }
        });
        this.charts = {};
        this.isInitialized = false;
        console.log("✅ All charts destroyed");
    }

    /**
     * FIXED: Resize all charts safely
     */
    resize() {
        Object.values(this.charts).forEach((chart) => {
            if (chart) {
                try {
                    chart.resize();
                } catch (error) {
                    console.error("❌ Error resizing chart:", error);
                }
            }
        });
    }

    /**
     * FIXED: Refresh all charts
     */
    async refreshAllCharts() {
        try {
            console.log("🔄 Refreshing all charts...");

            // Refresh price chart
            await this.updatePriceChart();

            // Refresh other charts by requesting fresh data from dashboard
            const dashboard = window.Dashboard;
            if (dashboard && dashboard.state.isInitialized) {
                await dashboard.loadStrategies();
                await dashboard.loadPortfolio();
            }

            console.log("✅ All charts refreshed");
        } catch (error) {
            console.error("❌ Error refreshing charts:", error);
        }
    }

    /**
     * FIXED: Check if all required charts are loaded
     */
    areChartsLoaded() {
        const requiredCharts = ["price", "strategy", "allocation"];
        return requiredCharts.every((chartKey) => this.charts[chartKey] !== undefined);
    }

    /**
     * Set chart loading state
     */
    setChartLoading(chartKey, isLoading = true) {
        const canvas = document.getElementById(chartKey + "-chart");

        if (canvas) {
            const container = canvas.parentElement;
            if (isLoading) {
                container.classList.add("loading");
            } else {
                container.classList.remove("loading");
            }
        }
    }

    /**
     * FIXED: Health check for chart manager
     */
    healthCheck() {
        const health = {
            isInitialized: this.isInitialized,
            chartsLoaded: Object.keys(this.charts).length,
            requiredCharts: this.areChartsLoaded(),
            updateFlags: this.updateFlags,
            errors: [],
        };

        // Check for chart errors
        const requiredCharts = ["price", "strategy", "allocation"];
        requiredCharts.forEach((chartKey) => {
            const chart = this.charts[chartKey];
            if (!chart) {
                health.errors.push(`Chart ${chartKey} not initialized`);
            }
        });

        // Check if Chart.js is available
        if (typeof Chart === "undefined") {
            health.errors.push("Chart.js library not loaded");
        }

        return health;
    }

    /**
     * Export chart as image
     */
    exportChart(chartKey, filename = "chart.png") {
        const chart = this.charts[chartKey];
        if (chart) {
            try {
                const url = chart.toBase64Image();
                const link = document.createElement("a");
                link.download = filename;
                link.href = url;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                console.log(`✅ Chart ${chartKey} exported as ${filename}`);
            } catch (error) {
                console.error(`❌ Error exporting chart ${chartKey}:`, error);
            }
        }
    }

    /**
     * Get chart statistics
     */
    getChartStats() {
        const stats = {};

        Object.keys(this.charts).forEach((chartKey) => {
            const chart = this.charts[chartKey];
            if (chart && chart.data) {
                stats[chartKey] = {
                    type: chart.config.type,
                    datasets: chart.data.datasets.length,
                    dataPoints: chart.data.datasets.reduce((total, dataset) => {
                        return total + (dataset.data ? dataset.data.length : 0);
                    }, 0),
                    labels: chart.data.labels ? chart.data.labels.length : 0,
                };
            }
        });

        return stats;
    }

    /**
     * Update chart theme (for dark/light mode toggle)
     */
    updateTheme(isDark = true) {
        const textColor = isDark ? "#a0aec0" : "#2d3748";
        const gridColor = isDark ? "#2d3748" : "#e2e8f0";

        Object.values(this.charts).forEach((chart) => {
            if (chart && chart.options) {
                // Update text colors
                if (chart.options.plugins?.legend?.labels) {
                    chart.options.plugins.legend.labels.color = textColor;
                }

                // Update scale colors
                if (chart.options.scales) {
                    Object.keys(chart.options.scales).forEach((scaleKey) => {
                        const scale = chart.options.scales[scaleKey];
                        if (scale.ticks) scale.ticks.color = textColor;
                        if (scale.grid) scale.grid.color = gridColor;
                    });
                }

                chart.update("none");
            }
        });
    }

    /**
     * Add chart animation on data update
     */
    animateChart(chartKey, animationType = "bounce") {
        const chart = this.charts[chartKey];
        if (chart) {
            chart.update(animationType);
        }
    }
}

// FIXED: Create global instance with proper initialization
window.ChartManager = new ChartManager();

// FIXED: Handle window resize properly
window.addEventListener("resize", () => {
    if (window.ChartManager && window.ChartManager.isInitialized) {
        window.ChartManager.resize();
    }
});

// FIXED: Initialize ChartManager when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    // Wait a bit for Chart.js to load
    setTimeout(() => {
        if (window.ChartManager) {
            const success = window.ChartManager.init();
            if (success) {
                console.log("✅ ChartManager ready for use");
            } else {
                console.error("❌ ChartManager failed to initialize");
            }
        }
    }, 1000);
});

// Export for module usage
if (typeof module !== "undefined" && module.exports) {
    module.exports = ChartManager;
}
