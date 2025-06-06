# 🍉Support Humanitarian Efforts in Palestine🍉

The ongoing humanitarian crisis in Palestine has left millions in urgent need of aid. If you're looking to make a difference, consider supporting trusted organizations working on the ground to provide food, medical care, and essential relief:
- [UN Crisis Relief – Occupied Palestinian Territory Humanitarian Fund](https://crisisrelief.un.org/en/opt-crisis)
- [Palestine Children's Relief Fund ](https://www.pcrf.net/)
- [Doctors Without Borders](https://www.doctorswithoutborders.org/)
- [Anera (American Near East Refugee Aid)](https://www.anera.org/)
- [Save the Children](https://www.savethechildren.org/us/where-we-work/west-bank-gaza)
Every contribution helps provide critical assistance to those affected. Learn more and donate through the links above.

<br></br>


# Odin - Professional Bitcoin Trading Bot (Updated)

<div align="center">

🚀 **Advanced Bitcoin Trading Bot with Real-Time Data, Live Trading & AI-Ready Architecture**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Production Ready](https://img.shields.io/badge/production-ready-brightgreen.svg)](#)
[![Real Data](https://img.shields.io/badge/real%20data-enabled-success.svg)](#)

</div>

## 🎯 Overview

**Odin** is a sophisticated, production-ready Bitcoin trading bot designed for live cryptocurrency trading with real-time data integration. Built with modern Python and FastAPI, it provides real-time Bitcoin data collection, multiple advanced trading strategies, live trade execution, comprehensive risk management, and a professional API with WebSocket support for real-time dashboard updates.

### ⚡ Latest Features (Recently Added)

- 🔴 **Real Bitcoin Data Integration** - Live data from Coinbase, CoinGecko, and Binance APIs
- 🔴 **WebSocket Real-Time Updates** - Stable WebSocket connections for live dashboard updates
- 🔴 **Complete Trading API** - All trading endpoints implemented (enable/disable, execute, emergency stop)
- 🔴 **Fixed Chart Rendering** - Optimized chart sizes prevent browser crashes
- 🔴 **Strategy Management** - Enable/disable individual strategies via API
- 🔴 **Auto-Trading Controls** - Complete auto-trading enable/disable functionality
- 🔴 **Performance Optimizations** - Memory-efficient data collection and chart rendering
- 🔴 **AI/ML Ready Architecture** - Foundation prepared for machine learning features

### 🚀 Core Features

- 🔄 **Live Trading System** - Real Bitcoin trading with exchange integration
- 📊 **Advanced Trading Strategies** - MA, RSI, Bollinger Bands, and MACD indicators
- 🛡️ **Production-Grade Architecture** - Modular API design, comprehensive testing
- 💰 **Portfolio Management** - Real-time tracking, P&L calculation, risk management
- 📈 **Strategy Optimization** - Live parameter tuning and performance analysis
- 🔌 **Professional API** - 40+ REST endpoints with comprehensive documentation
- 🌐 **Real-Time WebSocket** - Live price updates and trading notifications
- 🎨 **Modern Dashboard** - Responsive UI with real-time charts and controls
- 🔐 **Enterprise Security** - JWT authentication, rate limiting, comprehensive logging

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/jackfredericksen/Odin.git
cd Odin

# Copy environment template
cp .env.example .env

# Start with Docker Compose
docker-compose up -d

# Access the API
curl http://localhost:8000/api/v1/health
```

### Manual Installation

```bash
# Clone and setup
git clone https://github.com/jackfredericksen/Odin.git
cd Odin

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m odin.main

# Access dashboard at http://localhost:8000
```

## 📊 Real Bitcoin Data Sources

Odin now fetches live Bitcoin data from multiple sources with automatic failover:

1. **Coinbase API** - Primary source for price data
2. **CoinGecko API** - Secondary source with volume and 24h change
3. **Binance API** - Tertiary source for additional redundancy
4. **Mock Data Fallback** - Ensures system stability if all APIs fail

### Data Collection Features
- **30-second intervals** for real-time updates
- **Automatic source failover** if APIs are unavailable
- **1000-point rolling history** for efficient memory usage
- **Real-time WebSocket broadcasting** to dashboard clients
- **Historical data simulation** with realistic price movements

## 🔧 Complete API Endpoints

### **Real-Time Data (`/api/v1/data/`)**
```bash
GET    /current                        # Current Bitcoin price & metrics
GET    /history/{hours}                # Historical price data (real/simulated)
GET    /ohlc/{timeframe}               # OHLC candlestick data
GET    /stats                          # Data source statistics
POST   /refresh                        # Force data refresh
```

### **Auto-Trading Controls (`/api/v1/trading/`)**
```bash
POST   /enable                         # Enable auto-trading
POST   /disable                        # Disable auto-trading
GET    /status                         # Auto-trading status
PUT    /config                         # Update auto-trading config
POST   /emergency-stop                 # Emergency stop all trading
POST   /{strategy}/execute             # Execute trade for strategy
GET    /history                        # Trading history
```

### **Strategy Management (`/api/v1/strategies/`)**
```bash
GET    /list                           # List all strategies
POST   /{strategy_id}/enable           # Enable specific strategy
POST   /{strategy_id}/disable          # Disable specific strategy
PUT    /{strategy_id}/config           # Update strategy configuration
GET    /{strategy}/analysis            # Strategy analysis
GET    /{strategy}/backtest/{hours}    # Strategy backtesting
GET    /compare/all/{hours}            # Strategy comparison
```

### **Portfolio Management (`/api/v1/portfolio/`)**
```bash
GET    /                               # Portfolio status & overview
GET    /performance/{hours}            # Performance analytics
GET    /allocation                     # Current allocation breakdown
POST   /rebalance                      # Portfolio rebalancing
GET    /risk-metrics                   # Risk analysis & metrics
```

### **WebSocket Connection (`/ws`)**
- **Real-time price updates** from live Bitcoin APIs
- **Portfolio change notifications**
- **Trading signal alerts**
- **System status updates**
- **Connection management** with automatic reconnection

## 📊 Trading Strategies (Production Ready)

| **Strategy** | **Type** | **Best For** | **Signals** | **Parameters** | **Status** |
|--------------|----------|--------------|-------------|----------------|------------|
| **Moving Average (MA)** | Trend Following | Trending markets | Golden/Death Cross | Short: 5, Long: 20 | ✅ Implemented |
| **RSI Momentum** | Mean Reversion | Sideways markets | Overbought/Oversold | Period: 14, Levels: 30/70 | ✅ Implemented |
| **Bollinger Bands** | Volatility | Breakouts & reversions | Band touches | Period: 20, StdDev: 2 | ✅ Implemented |
| **MACD** | Trend Momentum | Trend changes | Line crossovers | Fast: 12, Slow: 26, Signal: 9 | ✅ Implemented |

### Live Strategy Features
- **Real-time signal generation** with confidence scoring
- **Live trade execution** with risk management integration
- **Performance attribution** across individual strategies
- **Dynamic parameter optimization** based on market conditions
- **Strategy comparison** with live vs backtest performance
- **Risk-adjusted returns** with Sharpe ratio calculation

## 💰 Live Trading Features

### Production Trading Engine
- **Real exchange integration** with live order placement
- **Multi-order types** - Market, Limit, Stop-Loss, Take-Profit
- **Risk management** - Position sizing, exposure limits, drawdown controls
- **Portfolio tracking** - Real-time P&L, positions, performance attribution
- **Automated trading** - Strategy-driven execution with safety controls
- **Emergency controls** - Immediate stop-all functionality

### Risk Management
- **Position limits** - Maximum 95% capital allocation per trade
- **Risk per trade** - Configurable risk limits (max 5% per trade)
- **Portfolio exposure** - Real-time monitoring and alerts
- **Stop-loss automation** - Dynamic stop-loss management
- **Drawdown protection** - Maximum drawdown controls

## 🌐 Real-Time Dashboard Features

### Fixed & Optimized UI
- **Chart size optimization** - Prevents browser crashes from oversized charts
- **Real-time WebSocket updates** - Live price and portfolio data
- **Strategy control panels** - Enable/disable strategies in real-time
- **Auto-trading toggles** - Control automated trading from dashboard
- **Emergency stop button** - Immediate halt of all trading activities
- **Performance monitoring** - Live strategy performance visualization

### Dashboard Sections
- **Price Chart** - Real-time Bitcoin price with technical indicators
- **Strategy Panel** - Live strategy status and performance metrics
- **Portfolio Allocation** - Real-time portfolio distribution
- **Recent Orders** - Live trading history and order status
- **System Status** - WebSocket connection, data sources, system health

## 🔐 Security & Authentication

### Enterprise-Grade Security
- **JWT Authentication** - Secure token-based authentication
- **Role-based access** - User/Admin permission levels
- **Rate limiting** - Per-endpoint request throttling
- **Input validation** - Comprehensive request validation
- **Security headers** - CORS, XSS, CSRF protection
- **Audit logging** - Complete trading operation logs

### Rate Limits
- **Data endpoints**: 60 requests/minute
- **Strategy endpoints**: 20 requests/minute
- **Trading endpoints**: 30 requests/minute
- **General endpoints**: 100 requests/minute

## 📈 Performance & Monitoring

### System Metrics (Optimized)
- **API Response Time**: <100ms average, <500ms 99th percentile
- **Data Collection**: 30-second intervals with automatic failover
- **Memory Usage**: ~150MB with real data and optimized charts
- **Strategy Processing**: <500ms for real-time analysis
- **Database Size**: ~2MB per day of price data
- **WebSocket Latency**: <50ms for live updates
- **Chart Rendering**: Optimized to prevent browser crashes

### Monitoring & Health Checks
- **System health** monitoring with detailed metrics
- **Database connectivity** and performance tracking
- **External API** status and response times (Coinbase, CoinGecko, Binance)
- **Trading engine** health and execution quality
- **Portfolio performance** tracking and attribution
- **WebSocket connection** monitoring and auto-reconnection

## 🚀 Deployment

### Docker Production Setup

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up --scale odin-api=3

# Monitor logs
docker-compose logs -f odin-api
```

### Environment Configuration

```bash
# Application Settings
ODIN_ENV=production
ODIN_HOST=0.0.0.0
ODIN_PORT=8000
ODIN_SECRET_KEY=your-secret-key

# Real Data Sources
COINBASE_API_ENABLED=true
COINGECKO_API_ENABLED=true
BINANCE_API_ENABLED=true
DATA_COLLECTION_INTERVAL=30

# Database
DATABASE_URL=postgresql://user:pass@localhost/odin_db

# Security
JWT_SECRET_KEY=your-jwt-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Trading
ENABLE_LIVE_TRADING=true
MAX_POSITION_SIZE=0.95
RISK_PER_TRADE=0.02

# Exchange API (for live trading)
EXCHANGE_API_KEY=your-exchange-api-key
EXCHANGE_SECRET_KEY=your-exchange-secret
EXCHANGE_SANDBOX=false
```


## 🧪 Testing

### Comprehensive Test Suite

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=odin --cov-report=html

# Run specific test categories
pytest tests/unit/                     # Unit tests
pytest tests/integration/              # Integration tests
pytest tests/performance/              # Performance tests

# Test real data integration
pytest tests/integration/test_data_collector.py
pytest tests/integration/test_websocket.py
```

## 🎯 Next Steps: AI/ML Integration Ready

The Odin architecture is now prepared for advanced AI/ML features:

- **Real-time data pipeline** for ML model training
- **Modular strategy framework** for AI strategy integration
- **Performance tracking** for ML model evaluation
- **Risk management** for AI trading decisions
- **WebSocket infrastructure** for real-time AI predictions

See the AI/ML Development Plan for detailed implementation roadmap.

## 📚 Documentation

### Available Documentation
- **[API Reference](docs/api.md)** - Complete endpoint documentation
- **[Deployment Guide](docs/deployment.md)** - Production setup instructions
- **[Strategy Development](docs/strategies.md)** - Custom strategy creation
- **[Architecture Overview](docs/architecture.md)** - System design details
- **[AI/ML Integration Plan](docs/ai-ml-plan.md)** - Machine learning roadmap

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 🤝 Contributing

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt
pip install aiohttp  # For real data collection

# Install pre-commit hooks
pre-commit install

# Run code formatting
black odin/ tests/
isort odin/ tests/
flake8 odin/ tests/

# Run type checking
mypy odin/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**Odin is for educational and research purposes. Cryptocurrency trading involves significant financial risk. Never trade with money you cannot afford to lose. Always test thoroughly with paper trading before using real funds. The AI/ML features are experimental and should be used with extreme caution.**

## 🙏 Acknowledgments

- **FastAPI** - Modern, fast web framework
- **Coinbase, CoinGecko, Binance** - Real-time Bitcoin data sources
- **Chart.js** - Beautiful data visualization
- **WebSocket** - Real-time communication
- **The Bitcoin Community** - Inspiration and support

---

<div align="center">

**Made with ❤️ for professional Bitcoin trading and AI/ML research**

[⭐ Star this repo](https://github.com/jackfredericksen/Odin) if you find it useful!

**Odin - Where Norse wisdom meets modern trading technology and artificial intelligence** ⚡🤖

</div>