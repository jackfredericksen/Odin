# Bitcoin Trading Bot

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
mkdir bitcoin-trader
cd bitcoin-trader
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create folder structure:**
```bash
mkdir -p config data src strategies web_interface scripts docs
touch src/__init__.py strategies/__init__.py
```

4. **Add the provided files to their respective folders**

## 🎯 Quick Start

1. **Start the API server:**
```bash
python src/api_server.py
```

2. **Open dashboard:**
Navigate to `http://localhost:5000` in your browser

3. **Watch live data:**
The system will automatically start collecting Bitcoin prices every 60 seconds

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

## 🔧 Configuration

Edit `config/settings.py` to customize:
- Moving average periods
- Data collection intervals
- Risk management parameters
- API settings

## 📝 Development Log

### ✅ **Phase 1: Foundation (Complete)**
- Multi-source data pipeline with automatic failover
- Real-time Bitcoin price collection every 60 seconds
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

### 🔄 **Next Development Priorities:**
1. **Paper Trading System** - Automated trade execution simulation
2. **Risk Management** - Stop-loss, take-profit, position sizing
3. **Alert System** - Email/SMS notifications for signals
4. **Strategy Optimization** - Parameter tuning and genetic algorithms
5. **Portfolio Management** - Multi-asset support and allocation

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Data Sources  │────│  API Server  │────│   Web Dashboard │
│ (Multi-fallback)│    │   (Flask)    │    │  (5 Strategies) │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │
                    ┌─────────────────────┐
                    │   Strategy Engine   │
                    │  MA │ RSI │ BB │ MACD │
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

## 🛡️ Risk Warning

This bot is for educational and testing purposes. Always:
- **Start with paper trading** - Never use real money initially
- **Test thoroughly** - Backtest strategies across different market conditions
- **Understand the risks** - Cryptocurrency trading involves significant risk
- **Never risk more than you can afford to lose**
- **Be aware of market volatility** - Bitcoin can be extremely volatile
- **Monitor performance** - Regularly review and adjust strategies
- **Consider tax implications** - Automated trading may have tax consequences

## 🎓 Educational Value

This project demonstrates:
- **Real-time data processing** and API integration
- **Multiple trading strategy implementations** and comparison
- **Modern web development** with responsive design
- **Database design** for financial time-series data
- **RESTful API architecture** and endpoint design
- **Backtesting methodology** and performance metrics
- **Professional dashboard development** with interactive visualizations

## 🤝 Contributing

This is an educational project showing professional-grade trading bot development. Feel free to:
- **Extend strategies** - Add new technical indicators
- **Improve UI/UX** - Enhance the dashboard design
- **Add features** - Implement additional functionality
- **Optimize performance** - Improve speed and efficiency
- **Add tests** - Implement comprehensive testing
