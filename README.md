# ⚡ Odin - Advanced Bitcoin Trading Bot

An advanced cryptocurrency trading bot with real-time data collection, multiple trading strategies, and a professional web-based dashboard.

## 🚀 Features

- **Live Bitcoin Data Collection** with multi-source fallback (CoinDesk → Blockchain.info → CoinGecko)
- **Four Advanced Trading Strategies** with real-time signal generation
- **Professional Web Dashboard** with interactive strategy switching and live charts
- **Strategy Performance Comparison** with live backtesting results
- **Historical Data Storage** in SQLite database
- **RESTful API** for data access and strategy analysis

## 📊 Trading Strategies

### 1. **Moving Average Crossover (MA)**
- **Strategy:** MA(5,20) crossover signals
- **Buy Signal:** 5-period MA crosses above 20-period MA (bullish trend)
- **Sell Signal:** 5-period MA crosses below 20-period MA (bearish trend)
- **Best For:** Trend-following in trending markets

### 2. **RSI (Relative Strength Index)**
- **Strategy:** RSI(14) momentum oscillator
- **Buy Signal:** RSI crosses above oversold threshold (< 30)
- **Sell Signal:** RSI crosses below overbought threshold (> 70)
- **Best For:** Mean reversion in sideways markets

### 3. **Bollinger Bands**
- **Strategy:** BB(20,2) volatility-based signals
- **Buy Signal:** Price touches or goes below lower band
- **Sell Signal:** Price touches or goes above upper band
- **Best For:** Volatility breakouts and mean reversion

### 4. **MACD (Moving Average Convergence Divergence)**
- **Strategy:** MACD(12,26,9) trend momentum
- **Buy Signal:** MACD line crosses above signal line, zero-line crossovers
- **Sell Signal:** MACD line crosses below signal line, histogram reversals
- **Best For:** Trend changes and momentum confirmation

## 🎯 Dashboard Features

### **Interactive Strategy Tabs:**
- **Moving Average** - Live trend analysis with MA overlay
- **RSI** - Momentum signals with overbought/oversold levels
- **Bollinger Bands** - Volatility analysis with %B indicator
- **MACD** - Trend momentum with histogram visualization
- **Compare All** - Real-time performance battle of all strategies

### **Live Visualizations:**
- Real-time Bitcoin price charts
- Strategy-specific indicators and overlays
- Signal strength indicators
- Performance metrics and win rates
- Live strategy ranking and winner detection

## 🛠️ Installation

1. **Clone or create project directory:**
```bash
mkdir odin-trading-bot
cd odin-trading-bot
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create folder structure:**
```bash
mkdir -p config data src strategies web_interface scripts docs backtesting
touch src/__init__.py strategies/__init__.py backtesting/__init__.py
```

4. **Add the provided files to their respective folders**

## 🎯 Quick Start

1. **Start the API server:**
```bash
python src/btc_api_server.py
```

2. **Open dashboard:**
Navigate to `http://localhost:5000` in your browser

3. **Watch live data:**
The system will automatically start collecting Bitcoin prices every 30 seconds

4. **Explore strategies:**
Click through the strategy tabs to see different trading approaches

## 📈 Strategy Performance Testing

### **Test Individual Strategies:**
```bash
python strategies/ma_crossover.py      # Moving Average strategy
python strategies/rsi_strategy.py      # RSI momentum strategy
python strategies/bollinger_bands.py   # Bollinger Bands volatility
python strategies/macd_strategy.py     # MACD trend momentum
```

### **Fetch Historical Data:**
```bash
python scripts/fetch_historical_data.py
```

### **Generate Sample Data (for testing):**
```bash
python scripts/generate_sample_data.py
```

## 🔌 API Endpoints

### **Price Data:**
- `GET /api/current` - Current Bitcoin price and stats
- `GET /api/history/{hours}` - Historical price data
- `GET /api/stats` - Overall statistics

### **Strategy Analysis:**
- `GET /api/strategy/ma/analysis` - Moving Average strategy analysis
- `GET /api/strategy/rsi/analysis` - RSI strategy analysis
- `GET /api/strategy/bb/analysis` - Bollinger Bands analysis
- `GET /api/strategy/macd/analysis` - MACD strategy analysis

### **Backtesting:**
- `GET /api/strategy/ma/backtest/{hours}` - MA strategy backtest
- `GET /api/strategy/rsi/backtest/{hours}` - RSI strategy backtest
- `GET /api/strategy/bb/backtest/{hours}` - Bollinger Bands backtest
- `GET /api/strategy/macd/backtest/{hours}` - MACD strategy backtest

### **Strategy Comparison:**
- `GET /api/strategy/compare/all/{hours}` - Compare all four strategies

## 📊 Data Sources

Primary sources with automatic fallback:
1. **CoinDesk API** (primary, completely free)
2. **Blockchain.info API** (fallback #1)
3. **CoinGecko API** (fallback #2)
4. **CryptoCompare API** (historical data)
5. **Yahoo Finance** (alternative historical source)

## 🔧 Configuration

Edit `config/settings.py` to customize:
- Moving average periods
- Data collection intervals (default: 30 seconds)
- Risk management parameters
- API settings
- RSI thresholds (oversold/overbought)
- Bollinger Bands parameters
- MACD periods

## 📝 Development Log

### ✅ **Phase 1: Foundation (Complete)**
- Multi-source data pipeline with automatic failover
- Real-time Bitcoin price collection every 30 seconds
- SQLite database with historical data storage
- RESTful API architecture with Flask

### ✅ **Phase 2: Core Strategies (Complete)**
- **Moving Average Crossover** - MA(5,20) trend-following strategy
- **RSI Strategy** - RSI(14) momentum oscillator with overbought/oversold signals
- **Bollinger Bands** - BB(20,2) volatility-based mean reversion strategy
- **MACD Strategy** - MACD(12,26,9) trend momentum with multiple signal types

### ✅ **Phase 3: Professional Dashboard (Complete)**
- Interactive 5-tab strategy switcher
- Real-time price charts with strategy-specific overlays
- Live signal generation with strength indicators
- Strategy performance comparison and ranking
- Responsive design with modern UI/UX

### ✅ **Phase 4: Advanced Analytics (Complete)**
- Live backtesting with configurable timeframes
- Strategy performance metrics (win rate, returns, trade count)
- Real-time strategy comparison and winner detection
- Signal strength visualization and confidence indicators
- Historical data fetching from multiple sources

### 🔄 **Next Development Priorities:**
1. **Paper Trading System** - Automated trade execution simulation
2. **Risk Management** - Stop-loss, take-profit, position sizing
3. **Alert System** - Email/SMS notifications for signals
4. **Strategy Optimization** - Parameter tuning and genetic algorithms
5. **Portfolio Management** - Multi-asset support and allocation
6. **Real Exchange Integration** - Connect to Binance, Coinbase Pro
7. **Machine Learning** - Price prediction and sentiment analysis

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │────│   API Server     │────│  Web Dashboard  │
│ (Multi-fallback)│    │ (btc_api_server) │    │  (5 Strategies) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                    ┌─────────────────────┐
                    │   Strategy Engine   │
                    │ MA │ RSI │ BB │ MACD│
                    └─────────────────────┘
                              │
                       ┌──────────────┐
                       │   Database   │
                       │   (SQLite)   │
                       └──────────────┘
```

## 📊 Performance Benchmarks

**Strategy Comparison (48-hour backtest example):**
- **MACD:** +2.8% return, 15 trades, 73% win rate
- **Bollinger Bands:** +2.1% return, 22 trades, 64% win rate  
- **RSI:** +1.9% return, 18 trades, 67% win rate
- **Moving Average:** +1.2% return, 8 trades, 75% win rate

*Results vary based on market conditions and timeframes*

# 📁 Updated Odin Project Structure

Based on your current implementation and planned features, here's the enhanced filesystem structure:

```
odin-trading-bot/
├── 📄 README.md
├── 📄 requirements.txt
├── 📄 .env.example                     # Environment variables template
├── 📄 docker-compose.yml               # Docker deployment
├── 📄 Dockerfile                       # Container configuration
│
├── ⚙️ config/
│   ├── __init__.py
│   ├── settings.py                     # Enhanced configuration system
│   ├── logging_config.py               # Logging configuration
│   └── api_keys.py                     # API key management
│
├── 🗄️ data/
│   ├── bitcoin_data.db                 # Historical price database (17+ years)
│   ├── trades.db                       # Trading history and performance
│   ├── portfolio.db                    # Portfolio tracking
│   ├── risk_metrics.db                 # Risk management data
│   └── backups/                        # Automated database backups
│       └── (auto-generated backups)
│
├── 🖥️ src/
│   ├── __init__.py
│   ├── btc_api_server.py               # Enhanced main API server
│   ├── data_collector.py               # Multi-source data collection
│   ├── data_manager.py                 # NEW: Historical + Live data integration
│   ├── portfolio_manager.py            # Portfolio tracking and management
│   ├── trade_executor.py               # Trade execution engine
│   └── utils/
│       ├── __init__.py
│       ├── database_utils.py           # Database utilities
│       ├── data_validation.py          # Data validation functions
│       └── crypto_utils.py             # Cryptographic utilities
│
├── 🧠 strategies/
│   ├── __init__.py
│   ├── base_strategy.py                # Base strategy class
│   ├── ma_crossover.py                 # Moving Average strategy (enhanced)
│   ├── rsi_strategy.py                 # RSI strategy (enhanced)
│   ├── bollinger_bands.py              # Bollinger Bands strategy (enhanced)
│   ├── macd_strategy.py                # MACD strategy (enhanced)
│   ├── multi_strategy.py               # NEW: Combined strategy signals
│   └── strategy_optimizer.py           # NEW: Parameter optimization
│
├── 🛡️ risk_management/
│   ├── __init__.py
│   ├── base_risk.py                    # Base risk management class
│   ├── risk_calculator.py              # Position sizing and risk metrics
│   ├── stop_loss_manager.py            # Dynamic stop-loss management
│   ├── portfolio_protector.py          # Portfolio-level risk controls
│   ├── drawdown_monitor.py             # Drawdown analysis and alerts
│   ├── exposure_manager.py             # Exposure and correlation analysis
│   └── var_calculator.py               # Value at Risk calculations
│
├── 📢 notifications/
│   ├── __init__.py
│   ├── base_notifier.py                # Base notification class
│   ├── email_notifier.py               # Email alerts (SMTP)
│   ├── sms_notifier.py                 # SMS notifications (Twilio)
│   ├── slack_notifier.py               # Slack integration
│   ├── discord_notifier.py             # Discord integration
│   ├── webhook_notifier.py             # Custom webhook alerts
│   ├── telegram_notifier.py            # Telegram bot integration
│   ├── notification_manager.py         # Centralized notification system
│   └── alert_rules.py                  # Alert rule engine
│
├── 📊 analytics/
│   ├── __init__.py
│   ├── performance_analyzer.py         # Trading performance metrics
│   ├── backtesting_engine.py           # Advanced backtesting system
│   ├── report_generator.py             # Automated performance reports
│   ├── market_analyzer.py              # Market condition analysis
│   ├── correlation_analyzer.py         # Asset correlation analysis
│   └── ml_predictor.py                 # Machine learning predictions
│
├── 🌐 web_interface/
│   ├── dashboard.html                  # Enhanced main dashboard
│   ├── risk_dashboard.html             # Risk management interface
│   ├── analytics_dashboard.html        # Performance analytics interface
│   ├── strategy_dashboard.html         # Strategy comparison interface
│   ├── portfolio_dashboard.html        # Portfolio management interface
│   ├── settings_dashboard.html         # Configuration interface
│   └── assets/
│       ├── css/
│       │   ├── main.css                # Main stylesheet
│       │   ├── dashboard.css           # Dashboard-specific styles
│       │   └── themes/                 # Multiple UI themes
│       │       ├── dark.css
│       │       ├── light.css
│       │       └── pro.css
│       ├── js/
│       │   ├── main.js                 # Main JavaScript
│       │   ├── charts.js               # Chart functionality
│       │   ├── websocket.js            # Real-time data connection
│       │   ├── notifications.js        # Browser notifications
│       │   └── utils.js                # Utility functions
│       ├── images/
│       │   ├── logo.png
│       │   ├── icons/                  # UI icons
│       │   └── charts/                 # Chart assets
│       └── fonts/                      # Custom fonts
│
├── 🔄 backtesting/
│   ├── __init__.py
│   ├── backtest_engine.py              # Core backtesting functionality
│   ├── performance_metrics.py          # Backtesting performance calculations
│   ├── scenario_generator.py           # Market scenario testing
│   ├── monte_carlo.py                  # Monte Carlo simulations
│   └── optimization/
│       ├── __init__.py
│       ├── genetic_algorithm.py        # Genetic algorithm optimization
│       ├── grid_search.py              # Grid search optimization
│       └── bayesian_optimization.py    # Bayesian optimization
│
├── 🛠️ scripts/
│   ├── __init__.py
│   ├── generate_sample_data.py         # Generate test data
│   ├── fetch_historical_data.py        # Historical data fetcher (enhanced)
│   ├── csv_to_db_converter.py          # CSV data import
│   ├── backup_manager.py               # Database backup utilities
│   ├── performance_optimizer.py        # System optimization
│   ├── verify_installation.py          # Installation verification
│   ├── migrate_database.py             # Database migration tools
│   ├── export_data.py                  # Data export utilities
│   └── deploy/
│       ├── __init__.py
│       ├── docker_deploy.py            # Docker deployment script
│       ├── aws_deploy.py               # AWS deployment
│       └── setup_server.py             # Server setup automation
│
├── 🧪 tests/
│   ├── __init__.py
│   ├── test_strategies.py              # Strategy testing
│   ├── test_risk_management.py         # Risk management testing
│   ├── test_data_collection.py         # Data collection testing
│   ├── test_notifications.py           # Notification testing
│   ├── test_api.py                     # API endpoint testing
│   ├── test_portfolio.py               # Portfolio management testing
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_full_system.py         # Full system integration tests
│   │   └── test_data_flow.py           # Data flow testing
│   └── fixtures/
│       ├── sample_data.json            # Test data fixtures
│       └── mock_responses.json         # Mock API responses
│
├── 📖 docs/
│   ├── README.md                       # Comprehensive documentation
│   ├── CHANGELOG.md                    # Version history
│   ├── CONTRIBUTING.md                 # Contribution guidelines
│   ├── api_documentation.md            # Complete API reference
│   ├── strategy_guide.md               # Strategy development guide
│   ├── risk_management_guide.md        # Risk management documentation
│   ├── deployment_guide.md             # Production deployment guide
│   ├── configuration_guide.md          # Configuration documentation
│   ├── troubleshooting.md              # Common issues and solutions
│   ├── performance_tuning.md           # Performance optimization
│   └── architecture/
│       ├── system_architecture.md      # System design documentation
│       ├── database_schema.md          # Database design
│       ├── api_design.md               # API architecture
│       └── security_model.md           # Security documentation
│
├── 🚀 deployment/
│   ├── docker/
│   │   ├── Dockerfile.prod             # Production Docker image
│   │   ├── Dockerfile.dev              # Development Docker image
│   │   └── docker-compose.yml          # Multi-container setup
│   ├── kubernetes/
│   │   ├── deployment.yaml             # Kubernetes deployment
│   │   ├── service.yaml                # Kubernetes service
│   │   └── configmap.yaml              # Configuration management
│   ├── terraform/
│   │   ├── main.tf                     # Infrastructure as code
│   │   ├── variables.tf                # Terraform variables
│   │   └── outputs.tf                  # Terraform outputs
│   └── scripts/
│       ├── deploy.sh                   # Deployment script
│       ├── backup.sh                   # Backup script
│       └── monitor.sh                  # Monitoring script
│
├── 📊 monitoring/
│   ├── __init__.py
│   ├── system_monitor.py               # System health monitoring
│   ├── performance_monitor.py          # Performance monitoring
│   ├── trade_monitor.py                # Trade execution monitoring
│   ├── alert_manager.py                # Alert management
│   └── dashboards/
│       ├── grafana/                    # Grafana dashboards
│       └── prometheus/                 # Prometheus configuration
│
├── 🔐 security/
│   ├── __init__.py
│   ├── encryption.py                   # Data encryption utilities
│   ├── api_auth.py                     # API authentication
│   ├── rate_limiter.py                 # Rate limiting
│   └── audit_log.py                    # Security audit logging
│
└── 📋 logs/
    ├── trading_bot.log                 # Main application logs
    ├── trades.log                      # Trade execution logs
    ├── errors.log                      # Error logs
    ├── performance.log                 # Performance logs
    ├── security.log                    # Security audit logs
    └── archived/                       # Archived log files
        └── (auto-archived logs)
```

## 📊 **Key Changes from Original Structure:**

### **New Major Additions:**
- **🛡️ risk_management/** - Complete risk management system
- **📢 notifications/** - Multi-channel notification system  
- **📊 analytics/** - Advanced analytics and ML predictions
- **🧪 tests/** - Comprehensive testing suite
- **🚀 deployment/** - Production deployment tools
- **📊 monitoring/** - System monitoring and alerting
- **🔐 security/** - Security and encryption utilities

### **Enhanced Existing Folders:**
- **🖥️ src/** - Added data_manager.py for data integration
- **🌐 web_interface/** - Multiple specialized dashboards
- **🛠️ scripts/** - Added deployment and migration tools
- **📖 docs/** - Comprehensive documentation structure

### **New Features Supported:**
- Historical + Live data integration
- Multi-dashboard web interface
- Comprehensive risk management
- Advanced notification system
- Production deployment ready
- Security and monitoring
- Machine learning integration
- Comprehensive testing

This structure supports your current needs while providing room for future enhancements and production deployment.
## 🚀 Running Odin

### **Method 1: Direct Python**
```bash
# Start the main server
python src/btc_api_server.py

# Open browser to: http://localhost:5000
```

### **Method 2: Test Individual Components**
```bash
# Test data collection
python src/btc_collector.py

# Test strategies
python strategies/ma_crossover.py
python strategies/rsi_strategy.py
python strategies/bollinger_bands.py
python strategies/macd_strategy.py

# Fetch historical data
python scripts/fetch_historical_data.py
```

## 🛡️ Risk Warning

Odin is for educational and testing purposes. Always:
- **Start with paper trading** - Never use real money initially
- **Test thoroughly** - Backtest strategies across different market conditions
- **Understand the risks** - Cryptocurrency trading involves significant risk
- **Never risk more than you can afford to lose**
- **Be aware of market volatility** - Bitcoin can be extremely volatile
- **Monitor performance** - Regularly review and adjust strategies
- **Consider tax implications** - Automated trading may have tax consequences

## 🎓 Educational Value

Odin demonstrates:
- **Real-time data processing** and API integration
- **Multiple trading strategy implementations** and comparison
- **Modern web development** with responsive design
- **Database design** for financial time-series data
- **RESTful API architecture** and endpoint design
- **Backtesting methodology** and performance metrics
- **Professional dashboard development** with interactive visualizations
- **Multi-source data fallback** and error handling
- **Strategy performance analysis** and comparison frameworks

## 🤝 Contributing

Odin is an educational project showing professional-grade trading bot development. Feel free to:
- **Extend strategies** - Add new technical indicators (Stochastic, Williams %R, etc.)
- **Improve UI/UX** - Enhance the dashboard design and user experience
- **Add features** - Implement paper trading, alerts, portfolio management
- **Optimize performance** - Improve speed and efficiency
- **Add tests** - Implement comprehensive testing suites
- **Documentation** - Improve code documentation and tutorials

## 🔧 Troubleshooting

### **Dashboard Not Loading:**
1. Check if API server is running: `python src/btc_api_server.py`
2. Verify port 5000 is not in use by another application
3. Check browser console for JavaScript errors
4. Ensure you have internet connection for external libraries

### **No Strategy Data:**
1. Wait for data collection (strategies need 20+ data points)
2. Run: `python scripts/fetch_historical_data.py` for instant historical data
3. Check database: Look for `data/bitcoin_data.db` file
4. Test individual strategies with their standalone Python files

### **API Errors:**
1. Check if CoinGecko/CoinDesk APIs are accessible
2. Verify your internet connection
3. Check for rate limiting (wait a few minutes)
4. Look at console output for specific error messages

## 📚 Learning Resources

**Technical Analysis:**
- Moving Averages: Trend following indicators
- RSI: Momentum oscillator for overbought/oversold conditions
- Bollinger Bands: Volatility and mean reversion analysis
- MACD: Trend momentum and signal line crossovers

**Python Trading:**
- pandas: Data manipulation and analysis
- numpy: Numerical computing for indicators
- Flask: Web framework for API development
- sqlite3: Database operations

**Web Development:**
- Chart.js: Interactive financial charts
- HTML/CSS/JavaScript: Dashboard development
- RESTful APIs: Data communication standards

## 🏆 Next Level Features

Coming soon to Odin:
- **Paper Trading Portfolio** - Virtual money management
- **Real Exchange Integration** - Live trading capabilities
- **Advanced Risk Management** - Stop-loss, position sizing
- **Machine Learning Signals** - AI-powered predictions
- **Multi-Asset Support** - Ethereum, Solana, and more
- **Mobile App** - Trading on the go
- **Social Features** - Strategy sharing and leaderboards

---

**⚡ Powered by Odin - Where Norse wisdom meets modern trading technology**