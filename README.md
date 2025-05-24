# Bitcoin Trading Bot

An advanced cryptocurrency trading bot with real-time data collection, strategy implementation, and web-based dashboard.

## 🚀 Features

- **Live Bitcoin Data Collection** with multi-source fallback (CoinDesk → Blockchain.info → CoinGecko)
- **Real-time Web Dashboard** with live price charts and moving averages
- **MA(5,20) Crossover Strategy** with buy/sell signal generation
- **Historical Data Storage** in SQLite database
- **Strategy Backtesting** with performance metrics
- **RESTful API** for data access and strategy analysis

## 📊 Dashboard Preview

- Live Bitcoin price with 24h change
- Moving average indicators (MA5, MA20)
- Buy/sell signals with colored badges
- Interactive price charts with strategy overlays
- Real-time trend analysis (BULLISH/BEARISH)

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

## 📈 Strategy Details

### Moving Average Crossover (MA 5,20)
- **Buy Signal:** When 5-period MA crosses above 20-period MA
- **Sell Signal:** When 5-period MA crosses below 20-period MA
- **Trend Detection:** Bullish when MA5 > MA20, Bearish when MA5 < MA20

### Backtesting Results
Run strategy analysis: `python strategies/ma_crossover.py`

## 🔌 API Endpoints

- `GET /api/current` - Current Bitcoin price and stats
- `GET /api/strategy/analysis` - Current strategy analysis
- `GET /api/strategy/backtest/{hours}` - Strategy backtest results
- `GET /api/history/{hours}` - Historical price data
- `GET /api/stats` - Overall statistics

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

- ✅ Data pipeline with multi-source fallback
- ✅ Real-time web dashboard
- ✅ MA crossover strategy implementation
- ✅ Strategy backtesting system
- ✅ RESTful API architecture
- 🔄 Paper trading system (planned)
- 🔄 Additional strategies (RSI, Bollinger Bands)
- 🔄 Risk management features

## 🛡️ Risk Warning

This bot is for educational and testing purposes. Always:
- Start with paper trading
- Never risk more than you can afford to lose
- Test strategies thoroughly before live trading
- Be aware of market volatility and risks

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Data Sources  │────│  API Server  │────│   Web Dashboard │
│ (Multi-fallback)│    │   (Flask)    │    │   (Real-time)   │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │
                       ┌──────────────┐
                       │   Strategy   │
                       │   Engine     │
                       └──────────────┘
                              │
                       ┌──────────────┐
                       │   Database   │
                       │   (SQLite)   │
                       └──────────────┘
```

## 📚 Next Steps

1. **Paper Trading System** - Simulate real trades
2. **Additional Strategies** - RSI, Bollinger Bands
3. **Risk Management** - Stop-loss, position sizing
4. **Alerts System** - Email/SMS notifications
5. **Performance Analytics** - Detailed reporting

## 📄 License

This project is for educational purposes. Use at your own risk.