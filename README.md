# 🍉Support Humanitarian Efforts in Palestine🍉

The ongoing humanitarian crisis in Palestine has left millions in urgent need of aid. If you're looking to make a difference, consider supporting trusted organizations working on the ground to provide food, medical care, and essential relief:
- [UN Crisis Relief – Occupied Palestinian Territory Humanitarian Fund](https://crisisrelief.un.org/en/opt-crisis)
- [Palestine Children's Relief Fund ](https://www.pcrf.net/)
- [Doctors Without Borders](https://www.doctorswithoutborders.org/)
- [Anera (American Near East Refugee Aid)](https://www.anera.org/)
- [Save the Children](https://www.savethechildren.org/us/where-we-work/west-bank-gaza)
<br></br>


# Odin - Professional Bitcoin Trading Bot

<div align="center">

🚀 **Advanced Bitcoin Trading Bot with Live Trading & Professional API Architecture**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Production Ready](https://img.shields.io/badge/production-ready-brightgreen.svg)](#)
[![Dashboard Working](https://img.shields.io/badge/dashboard-fully_functional-success.svg)](#)

</div>

## 🎯 Overview

**Odin** is a sophisticated, production-ready Bitcoin trading bot designed for live cryptocurrency trading. Built with modern Python and FastAPI, it provides real-time data collection, multiple advanced trading strategies, live trade execution, and a comprehensive web dashboard for professional Bitcoin trading operations.

### ⚡ Key Features

- 🔄 **Live Trading System** - Real Bitcoin trading with exchange integration
- 📊 **Advanced Trading Strategies** - MA, RSI, Bollinger Bands, and MACD indicators
- 🛡️ **Production-Grade Architecture** - Modular API design, comprehensive testing
- 💰 **Portfolio Management** - Real-time tracking, P&L calculation, risk management
- 📈 **Strategy Optimization** - Live parameter tuning and performance analysis
- 🔌 **Professional API** - 50+ REST endpoints with comprehensive documentation
- 🌐 **Interactive Dashboard** - Full-featured web interface with real-time updates
- 🔐 **Enterprise Security** - JWT authentication, rate limiting, comprehensive logging
- 📡 **WebSocket Support** - Real-time price feeds, trading signals, and notifications
- 🤖 **AI Enhancement** - Machine learning regime detection and adaptive strategy selection

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

# Access the dashboard
open http://localhost:8000
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

## 🏗️ Complete Project Structure

```
Odin/
├── odin_cli.py
├── cli_launcher.sh
├── README.md                           # This documentation
├── requirements.txt                    # Python dependencies
├── requirements-dev.txt                # Development dependencies  
├── pyproject.toml                      # Modern Python project config
├── .env.example                        # Environment template
├── .gitignore                          # Git ignore rules
├── docker-compose.yml                  # Docker development environment
├── Dockerfile                          # Container definition
├── LICENSE                             # MIT license
│
├── odin/                               # Main application package
│   ├── __init__.py                     # Package initialization
│   ├── main.py                         # Application entry point
│   ├── config.py                       # Configuration management
│   │
│   ├── api/                            # FastAPI web layer
│   │   ├── __init__.py                 # API package init
│   │   ├── app.py                      # FastAPI application setup
│   │   ├── dependencies.py             # Dependency injection container
│   │   ├── middleware.py               # Auth, rate limiting, security
│   │   └── routes/                     # API route handlers
│   │       ├── __init__.py             # Routes package init
│   │       ├── data.py                 # Bitcoin data endpoints
│   │       ├── health.py               # Health check endpoints
│   │       ├── websockets.py           # WebSocket real-time updates
│   │       ├── strategies.py           # Strategy management API
│   │       ├── trading.py              # Trading control API
│   │       ├── portfolio.py            # Portfolio management API
│   │       │
│   │       ├── strategies/             # Legacy strategy endpoints
│   │       │   ├── analysis.py         # Strategy analysis & charts
│   │       │   ├── backtesting.py      # Backtesting endpoints
│   │       │   ├── comparison.py       # Strategy comparison
│   │       │   ├── optimization.py     # Parameter optimization
│   │       │   ├── signals.py          # Signal management
│   │       │
│   │       ├── trading/                # Legacy trading endpoints
│   │       │   ├── execution.py        # Live trade execution
│   │       │   ├── orders.py           # Order management
│   │       │   └── positions.py        # Position management
│   │       │
│   │       ├── portfolio/              # Legacy portfolio endpoints
│   │       │   ├── status.py           # Portfolio status
│   │       │   ├── performance.py      # Performance analytics
│   │       │   └── risk.py             # Risk management
│   │       │
│   │       ├── market/                 # Market data endpoints
│   │       │   ├── regime.py           # Market regime analysis
│   │       │   ├── alerts.py           # Market alerts
│   │       │   └── depth.py            # Order book data
│   │       │
│   │       └── ai/                     # AI enhancement endpoints
│   │           └── regime.py           # AI regime detection API
│   │
│   ├── core/                           # Core business logic
│   │   ├── __init__.py                 # Core package init
│   │   ├── trading_engine.py           # Live trade execution engine
│   │   ├── portfolio_manager.py        # Portfolio operations & tracking
│   │   ├── risk_manager.py             # Risk management & controls
│   │   ├── data_collector.py           # Real-time Bitcoin data collection
│   │   ├── database.py                 # Database operations & models
│   │   ├── exceptions.py               # Custom exception classes
│   │   ├── models.py                   # Pydantic data models
│   │   └── config.py                   # Core configuration
│   │
│   ├── strategies/                     # Trading strategy implementations
│   │   ├── __init__.py                 # Strategies package init
│   │   ├── base.py                     # Abstract base strategy class
│   │   ├── moving_average.py           # MA crossover strategy
│   │   ├── rsi.py                      # RSI momentum strategy
│   │   ├── bollinger_bands.py          # Bollinger Bands volatility strategy
│   │   ├── macd.py                     # MACD trend momentum strategy
│   │   ├── ai_adaptive.py              # AI-enhanced adaptive strategy
│   │   ├── swing_trader.py
│   │   └── ai_enhanced/                # AI strategy modules
│   │
│   ├── ai/                             # AI enhancement features
│   │   ├── __init__.py                 # AI package init
│   │   ├── regime_detection/           # Market regime detection
│   │   │   ├── regime_detector.py      # ML regime detection
│   │   │   ├── market_states.py        # Market state definitions
│   │   │   └── regime_visualizer.py    # Regime visualization
│   │   └── strategy_selection/         # Adaptive strategy selection
│   │       └── adaptive_manager.py     # AI strategy manager
│   │
│   └── utils/                          # Utility functions and helpers
│       ├── __init__.py                 # Utils package init
│       ├── logging.py                  # Logging configuration
│       └── validators.py               # Input validation helpers
│
├── web/                                # Frontend web interface
│   ├── static/                         # Static assets
│   │   ├── css/
│   │   │   ├── dashboard.css           # Main dashboard styling
│   │   │   ├── components.css          # Reusable component styles
│   │   │   └── responsive.css          # Mobile responsive styles
│   │   ├── js/
│   │   │   ├── dashboard.js            # Main dashboard functionality
│   │   │   ├── charts.js               # Chart.js configurations
│   │   │   ├── websockets.js           # Real-time data handling
│   │   │   └── strategies.js           # Strategy management UI
│   │   └── images/
│   │       ├── logo.png                # Odin logo
│   │       └── favicon.ico             # Browser favicon
│   └── templates/                      # HTML templates
│       └── dashboard.html              # Main trading dashboard
│
├── tests/                              # Comprehensive test suite
│   ├── __init__.py                     # Test package init
│   ├── conftest.py                     # Pytest configuration & fixtures
│   ├── unit/                           # Unit tests
│   │   ├── test_strategies.py          # Strategy unit tests
│   │   ├── test_trading_engine.py      # Trading engine tests
│   │   ├── test_portfolio_manager.py   # Portfolio manager tests
│   │   ├── test_data_collector.py      # Data collection tests
│   │   └── test_api.py                 # API endpoint tests
│   ├── integration/                    # Integration tests
│   │   ├── test_full_system.py         # End-to-end system tests
│   │   ├── test_api_integration.py     # API integration tests
│   │   └── test_trading_flow.py        # Live trading flow tests
│   └── performance/                    # Performance benchmarks
│       ├── test_strategy_speed.py      # Strategy execution speed
│       ├── test_api_performance.py     # API response times
│       └── test_data_processing.py     # Data processing speed
│
├── scripts/                            # Utility and deployment scripts
│   ├── setup.py                        # Project setup and initialization
│   ├── migrate.py                      # Database migration script
│   ├── deploy.py                       # Production deployment script
│   ├── generate_data.py                # Generate sample test data
│   └── performance_monitor.py          # System performance monitoring
│
├── docs/                               # Project documentation
│   ├── api.md                          # Complete API documentation
│   ├── deployment.md                   # Production deployment guide
│   ├── strategies.md                   # Trading strategy documentation
│   └── architecture.md                 # System architecture overview
│
├── .github/workflows/                  # CI/CD automation
│   ├── ci.yml                          # Continuous integration
│   ├── deploy.yml                      # Deployment workflow
│   └── tests.yml                       # Automated testing
│
├── docker/                             # Docker configuration files
│   ├── app.dockerfile                  # Application container
│   ├── nginx.dockerfile                # Web server container
│   └── postgres.dockerfile             # Database container
│
├── config/                             # Configuration files
│   ├── development.yml                 # Development environment config
│   ├── production.yml                  # Production environment config
│   └── logging.yml                     # Logging configuration
│
└── data/                               # Data storage directory
    ├── bitcoin_data.db                 # SQLite database (auto-generated)
    ├── logs/                           # Application logs
    └── backups/                        # Database backups
```

## 📊 File Count Summary

| **Category** | **Files** | **Purpose** |
|--------------|-----------|-------------|
| **API Routes** | 23 files | Complete REST API + WebSocket endpoints |
| **Core Logic** | 9 files | Business logic & engines |
| **Strategies** | 6 files | Trading strategy implementations |
| **AI Features** | 8 files | Machine learning enhancements |
| **Tests** | 12 files | Comprehensive test coverage |
| **Frontend** | 8 files | Web interface & dashboard |
| **Configuration** | 8 files | Environment & deployment config |
| **Documentation** | 6 files | Complete project documentation |
| **Scripts** | 6 files | Utility & deployment scripts |
| **Docker** | 4 files | Containerization & deployment |
| **GitHub Actions** | 3 files | CI/CD automation |
| **Root Files** | 9 files | Project configuration |
| **Total** | **102 files** | **Professional codebase** |

## 🔧 Complete API Endpoints (50+ Routes)

### **Strategy Management (`/api/v1/strategies/`)**
```bash
GET    /list                           # List all strategies
GET    /{strategy_id}/chart/{hours}    # Chart data with indicators
POST   /{strategy_id}/backtest/{hours} # Strategy backtesting
POST   /{strategy_id}/optimize         # Parameter optimization
POST   /{strategy_id}/enable           # Enable strategy
POST   /{strategy_id}/disable          # Disable strategy
GET    /compare/all/{hours}            # Strategy comparison
GET    /leaderboard                    # Performance rankings
```

#### **Live Trading (`/api/v1/trading/`)**
```bash
GET    /history                        # Trading history
GET    /status                         # Auto-trading status
POST   /enable                         # Enable auto-trading
POST   /disable                        # Disable auto-trading
GET    /active                         # Active orders
GET    /positions                      # Current positions
POST   /emergency-stop                 # Emergency stop all trading
```

#### **Portfolio Management (`/api/v1/portfolio/`)**
```bash
GET    /                               # Portfolio overview
GET    /summary                        # Portfolio summary metrics
GET    /allocation                     # Current allocation breakdown
GET    /performance/{hours}            # Performance analytics
POST   /rebalance                      # Portfolio rebalancing
GET    /risk-metrics                   # Risk analysis & metrics
```

#### **Real-time Data (`/api/v1/data/`)**
```bash
GET    /current                        # Current Bitcoin price & metrics
GET    /history/{hours}                # Historical price data
GET    /ohlc/{timeframe}               # OHLC candlestick data
GET    /stats                          # Statistical analysis
POST   /refresh                        # Force data refresh
GET    /export/{format}                # Export data (CSV/JSON/XLSX)
```

#### **WebSocket Endpoints (`/api/v1/ws/`)**
```bash
WS     /data                           # Real-time price updates
WS     /portfolio                      # Portfolio live updates
WS     /signals                        # Trading signal notifications
WS     /status                         # System status updates
```

#### **Health & Monitoring (`/api/v1/health/`)**
```bash
GET    /                               # Basic health check
GET    /detailed                       # Comprehensive health status
GET    /database                       # Database connectivity
GET    /metrics                        # System performance metrics
```

## 📈 Trading Strategies

### Professional Strategy Suite

| **Strategy** | **Type** | **Best For** | **Signals** | **Parameters** |
|--------------|----------|--------------|-------------|----------------|
| **Moving Average (MA)** | Trend Following | Trending markets | Golden/Death Cross | Short: 5, Long: 20 |
| **RSI Momentum** | Mean Reversion | Sideways markets | Overbought/Oversold | Period: 14, Levels: 30/70 |
| **Bollinger Bands** | Volatility | Breakouts & reversions | Band touches | Period: 20, StdDev: 2 |
| **MACD** | Trend Momentum | Trend changes | Line crossovers | Fast: 12, Slow: 26, Signal: 9 |
| **AI Adaptive** | Machine Learning | All market conditions | ML predictions | Dynamic parameters |

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

## 🌐 Interactive Dashboard

### Full-Featured Web Interface
- **Real-time price charts** with technical indicators
- **Strategy management** - Enable/disable, configure parameters
- **Live trading controls** - Start/stop trading, emergency stops
- **Portfolio overview** - Balance, P&L, allocation visualization
- **Performance analytics** - Strategy comparison, optimization results
- **Risk monitoring** - Exposure limits, drawdown tracking
- **Trade history** - Complete trading log with filters
- **WebSocket updates** - Real-time data without page refresh

### Dashboard Features
- **📊 Interactive Charts** - TradingView-style price charts
- **⚡ Real-time Updates** - Live price feeds and portfolio changes
- **🎛️ Strategy Controls** - One-click enable/disable strategies
- **📈 Performance Metrics** - Sharpe ratio, drawdown, win rate
- **🔄 Portfolio Rebalancing** - Automated allocation management
- **📱 Responsive Design** - Works on desktop, tablet, and mobile
- **🔔 Notifications** - Trading alerts and system status

## 🤖 AI Enhancement Features

### Machine Learning Integration
- **Market Regime Detection** - Identify bull/bear/sideways markets
- **Adaptive Strategy Selection** - ML-driven strategy switching
- **Dynamic Parameter Optimization** - AI-powered parameter tuning
- **Sentiment Analysis** - News and social media sentiment
- **Pattern Recognition** - Chart pattern identification
- **Risk Prediction** - ML-based risk assessment

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

### System Metrics
- **API Response Time**: <100ms average, <500ms 99th percentile
- **Data Collection**: 30-second intervals with failover
- **Memory Usage**: ~150MB with full dataset
- **Strategy Processing**: <500ms for real-time analysis
- **Database Size**: ~2MB per day of price data
- **WebSocket Latency**: <50ms for live updates

### Comprehensive Health Checks
- **System health** monitoring with detailed metrics
- **Database connectivity** and performance tracking
- **External API** status and response times
- **Trading engine** health and execution quality
- **Portfolio performance** tracking and attribution
- **Kubernetes-ready** liveness and readiness probes

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

# Run strategy-specific tests
pytest tests/unit/test_strategies.py
pytest tests/integration/test_trading_flow.py
```

### Test Coverage
- **Unit tests** - Individual component testing
- **Integration tests** - End-to-end system testing
- **Performance tests** - Load and speed testing
- **Strategy tests** - Trading strategy validation
- **API tests** - Endpoint testing and validation

## 📚 Documentation

### Available Documentation
- **[API Reference](docs/api.md)** - Complete endpoint documentation
- **[Deployment Guide](docs/deployment.md)** - Production setup instructions
- **[Strategy Development](docs/strategies.md)** - Custom strategy creation
- **[Architecture Overview](docs/architecture.md)** - System design details

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 🎯 Access URLs

Once running, access these URLs:

```
📊 Dashboard:          http://localhost:8000
📖 API Documentation:  http://localhost:8000/docs
📋 Alternative Docs:   http://localhost:8000/redoc
💚 Health Check:       http://localhost:8000/api/v1/health
₿  Bitcoin Data:       http://localhost:8000/api/v1/data/current
💼 Portfolio:          http://localhost:8000/api/v1/portfolio
📈 Strategies:         http://localhost:8000/api/v1/strategies/list
```

## 🤝 Contributing

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run code formatting
black odin/ tests/
isort odin/ tests/
flake8 odin/ tests/

# Run type checking
mypy odin/
```

### Code Quality Standards
- **Code formatting**: Black, isort
- **Linting**: Flake8, mypy
- **Testing**: >90% coverage required
- **Documentation**: All public APIs documented
- **Security**: No hardcoded secrets, input validation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**Odin is for educational and research purposes. Cryptocurrency trading involves significant financial risk. Never trade with money you cannot afford to lose. Always test thoroughly with paper trading before using real funds.**

## 🙏 Acknowledgments

- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - Robust database operations
- **Pydantic** - Data validation and settings
- **Chart.js** - Beautiful data visualization
- **The Bitcoin Community** - Inspiration and support

## 🆕 What's New in v2.0

### ✨ Major Features Added:
- **🌐 Complete Dashboard Functionality** - All buttons and features now work
- **📡 WebSocket Real-time Updates** - Live price feeds and notifications
- **🎛️ Strategy Management UI** - Enable/disable, backtest, optimize strategies
- **💼 Portfolio Management** - Rebalancing, performance analytics, risk metrics
- **🔄 Trading Controls** - Start/stop trading, view positions, emergency stops
- **🖥️ Windows Compatibility** - No more Unicode encoding errors
- **🔍 Comprehensive Health Checks** - Detailed startup diagnostics
- **🤖 AI Enhancement Ready** - Machine learning framework integrated
- **📊 50+ API Endpoints** - Complete REST API with documentation
- **🛡️ Production Ready** - Enterprise security and monitoring

### 🔧 Technical Improvements:
- **Fixed all import issues** - Clean, working codebase
- **Added missing API routes** - Dashboard fully functional
- **WebSocket implementation** - Real-time data streaming
- **Comprehensive error handling** - Graceful fallbacks
- **Better logging system** - Windows-compatible output
- **Enhanced configuration** - Flexible environment setup

---

<div align="center">

**Made with ❤️ for professional Bitcoin trading**

[⭐ Star this repo](https://github.com/jackfredericksen/Odin) if you find it useful!

**Odin v2.0 - Where Norse wisdom meets modern trading technology** ⚡

</div>
│   │