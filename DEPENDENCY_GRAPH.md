# Odin Trading Bot - Dependency Graph & Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Interface                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dashboard   │  │   Charts     │  │  WebSockets  │          │
│  │  (HTML/JS)   │  │  (Chart.js)  │  │   (Real-time)│          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                    ┌────────▼────────┐
                    │   FastAPI App   │
                    │   (app.py)      │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │   API     │     │Middleware │     │WebSocket  │
    │  Routes   │     │  (Auth,   │     │ Manager   │
    │           │     │ Logging)  │     │           │
    └─────┬─────┘     └───────────┘     └─────┬─────┘
          │                                    │
    ┌─────▼─────────────────────────────┐      │
    │      Core Business Logic          │      │
    │  ┌──────────┐  ┌──────────┐       │      │
    │  │ Trading  │  │Portfolio │       │      │
    │  │ Engine   │  │ Manager  │       │      │
    │  └────┬─────┘  └────┬─────┘       │      │
    │       │             │              │      │
    │  ┌────▼─────┐  ┌───▼──────┐       │      │
    │  │   Risk   │  │   Data   │       │      │
    │  │ Manager  │  │Collector │       │      │
    │  └──────────┘  └────┬─────┘       │      │
    └─────────────────────┼─────────────┘      │
                          │                    │
    ┌─────────────────────┼────────────────────┘
    │                     │
    │  ┌──────────────────▼──────────────────┐
    │  │        Strategy Layer               │
    │  │  ┌────────┐  ┌────────┐  ┌────────┐│
    │  │  │   MA   │  │  RSI   │  │  MACD  ││
    │  │  │Strategy│  │Strategy│  │Strategy││
    │  │  └────────┘  └────────┘  └────────┘│
    │  │  ┌────────┐  ┌────────────────────┐│
    │  │  │Bollinger│  │  AI Adaptive      ││
    │  │  │ Bands  │  │  Strategy         ││
    │  │  └────────┘  └────────────────────┘│
    │  └─────────────────────────────────────┘
    │
    └──────────────────┬──────────────────
                       │
              ┌────────▼────────┐
              │    Database     │
              │   (SQLite)      │
              │  ┌────────────┐ │
              │  │  Prices    │ │
              │  │  Trades    │ │
              │  │ Strategies │ │
              │  │  Signals   │ │
              │  │ Portfolio  │ │
              │  └────────────┘ │
              └─────────────────┘
```

## Module Dependencies

### 1. API Layer (`odin/api/`)

#### `app.py` - FastAPI Application
**Depends on:**
- `odin.config` - Application configuration
- `odin.core.database` - Database manager
- `odin.core.data_collector` - Real-time data collection
- `odin.core.trading_engine` - Trading operations
- `odin.core.portfolio_manager` - Portfolio tracking
- `odin.api.routes.*` - All route modules
- `odin.api.middleware` - Authentication & security
- `odin.utils.logging` - Structured logging
- `odin.utils.cache` - Response caching

**Provides:**
- FastAPI application instance
- Route registration
- Middleware setup
- CORS configuration
- Static file serving

#### `middleware.py` - Security & Auth
**Depends on:**
- `fastapi` - Request/response handling
- `jose` - JWT token handling

**Provides:**
- Authentication middleware
- Rate limiting
- Security headers
- Request logging

### 2. Core Layer (`odin/core/`)

#### `trading_engine.py` - Trading Execution
**Depends on:**
- `odin.core.database` - Trade persistence
- `odin.core.risk_manager` - Risk checks
- `odin.core.portfolio_manager` - Portfolio updates
- `odin.strategies.*` - Strategy signals

**Provides:**
- Order execution (market, limit, stop-loss)
- Trade lifecycle management
- Exchange integration
- Emergency stop functionality

#### `portfolio_manager.py` - Portfolio Tracking
**Depends on:**
- `odin.core.database` - Portfolio data storage
- `odin.core.models` - Data models

**Provides:**
- Real-time P&L calculation
- Position tracking
- Performance metrics
- Portfolio snapshots
- Allocation management

#### `risk_manager.py` - Risk Controls
**Depends on:**
- `odin.core.portfolio_manager` - Current positions
- `odin.core.database` - Historical data

**Provides:**
- Position sizing
- Exposure limits
- Drawdown protection
- Risk per trade calculations

#### `data_collector.py` - Market Data
**Depends on:**
- `aiohttp` - Async HTTP client
- `odin.core.database` - Data persistence
- `odin.utils.cache` - API response caching

**Provides:**
- Real-time price collection
- Multi-exchange data aggregation
- OHLC data generation
- Market depth collection

#### `database.py` - Data Persistence
**Depends on:**
- `sqlite3` - Database driver
- `odin.core.models` - Data schemas

**Provides:**
- Database initialization
- CRUD operations for all tables
- Query methods
- Transaction management
- Foreign key constraints

### 3. Strategy Layer (`odin/strategies/`)

#### `base.py` - Base Strategy Class
**Depends on:**
- `abc` - Abstract base class
- `odin.core.models` - Signal models

**Provides:**
- Abstract strategy interface
- Common indicator calculations
- Signal generation framework

#### Strategy Implementations
All strategies depend on:
- `odin.strategies.base` - Base class
- `odin.core.database` - Historical data
- `pandas` / `numpy` - Data processing

**Moving Average (`moving_average.py`)**
- Golden cross / Death cross signals
- Configurable MA periods

**RSI (`rsi.py`)**
- Overbought/oversold signals
- Mean reversion strategy

**Bollinger Bands (`bollinger_bands.py`)**
- Volatility breakout signals
- Band touch detection

**MACD (`macd.py`)**
- Trend momentum signals
- MACD line crossovers

**AI Adaptive (`ai_adaptive.py`)**
- Market regime detection
- Dynamic strategy selection

### 4. Utility Layer (`odin/utils/`)

#### `logging.py` - Structured Logging
**Depends on:**
- `logging` - Standard library
- `json` - Log formatting
- `uuid` - Correlation IDs

**Provides:**
- `OdinLogger` class
- Structured JSON logging
- Correlation ID tracking
- Operation timing
- Context management

#### `cache.py` - API Response Caching
**Depends on:**
- `asyncio` - Async operations
- `hashlib` - Cache key generation

**Provides:**
- `CacheManager` class
- `@cached` decorator
- TTL support
- LRU eviction
- Cache statistics

### 5. Web Layer (`web/`)

#### JavaScript Dependencies

**`dashboard.js`** - Original Dashboard
**Depends on:**
- jQuery
- Chart.js
- WebSocket API

**`analytics-dashboard.js`** - Enhanced Dashboard
**Depends on:**
- Chart.js (price charts)
- Plotly.js (heatmaps, 3D charts)
- `logger.js` (structured logging)
- Fetch API (data loading)

**Provides:**
- Multi-coin support (7 cryptocurrencies)
- Real-time price updates
- Technical indicators
- Market sentiment analysis
- Pattern recognition

**`logger.js`** - JavaScript Logging
**Provides:**
- `LoggerFactory` singleton
- Structured console logging
- Correlation IDs
- Color-coded output
- Optional backend reporting

**`charts.js`** - Chart Configurations
**Depends on:**
- Chart.js

**Provides:**
- Reusable chart templates
- Theme configurations
- Responsive chart settings

**`websockets.js`** - Real-time Updates
**Depends on:**
- WebSocket API

**Provides:**
- Live price streaming
- Trading signal notifications
- Portfolio updates
- Reconnection logic

## Data Flow Diagrams

### Price Data Collection Flow
```
External APIs          Data Collector       Cache Layer       Database
    (Kraken,      ──►   (Real-time)    ──►  (10s TTL)   ──►  (SQLite)
     CoinGecko,           Collection
     Coinbase)
                             │
                             ▼
                        WebSocket    ──►    Dashboard
                        Broadcast         (Live Updates)
```

### Trading Signal Flow
```
Market Data    ──►   Strategies    ──►   Trading Engine   ──►   Exchange
                     (MA, RSI,           (Order Creation)      (Execution)
                      MACD, etc.)             │
                                              ▼
                                      Portfolio Manager  ──►  Database
                                      (P&L Tracking)        (Persistence)
                                              │
                                              ▼
                                        Risk Manager
                                        (Safety Checks)
```

### Dashboard Data Flow
```
User Browser   ──►   FastAPI Routes   ──►   Core Logic   ──►   Database
(Dashboard)          (API Endpoints)        (Business)         (Storage)
     ▲                      │
     │                      ▼
     └──────────────   Cache Layer
       (Real-time)      (Response Caching)
```

## Dependency Installation Order

### Python Dependencies
```
1. Core frameworks:
   - fastapi
   - uvicorn[standard]
   - pydantic

2. Data processing:
   - pandas
   - numpy
   - ta (technical analysis)

3. Database:
   - sqlalchemy (optional, currently using raw SQLite)

4. HTTP & WebSockets:
   - aiohttp
   - python-socketio
   - websockets

5. Security:
   - python-jose[cryptography]
   - passlib[bcrypt]

6. Development:
   - black (formatting)
   - isort (import sorting)
   - flake8 (linting)
   - mypy (type checking)
   - pytest (testing)
```

### JavaScript Dependencies
```
1. Chart.js (^3.9.1) - Core charting
2. Plotly.js (^2.18.0) - Advanced visualizations
3. jQuery (^3.6.0) - DOM manipulation (legacy)
```

## Import Chain Examples

### Trading Engine Import Chain
```
main.py
  └── odin.api.app
       └── odin.core.trading_engine
            ├── odin.core.database
            ├── odin.core.risk_manager
            │    └── odin.core.portfolio_manager
            │         └── odin.core.database
            └── odin.strategies.base
                 ├── odin.strategies.moving_average
                 ├── odin.strategies.rsi
                 ├── odin.strategies.macd
                 └── odin.strategies.bollinger_bands
```

### API Route Import Chain
```
main.py
  └── odin.api.app
       ├── odin.api.middleware
       │    └── odin.utils.logging
       └── odin.api.routes.data
            ├── odin.core.data_collector
            │    ├── odin.core.database
            │    └── odin.utils.cache
            └── odin.utils.logging
```

## Circular Dependency Prevention

### Current Strategy
1. **Database as Foundation** - No dependencies on other core modules
2. **Models Layer** - Pure data structures, no business logic
3. **Dependency Injection** - Pass dependencies via constructors
4. **Event-Driven** - Use callbacks instead of direct imports where possible

### Avoided Circular Dependencies
- `trading_engine` ↔ `portfolio_manager` - Resolved via database as intermediary
- `strategies` ↔ `data_collector` - Strategies read from database, not directly from collector
- `api.routes` ↔ `core` - One-way dependency (routes → core)

## External Dependencies

### API Integrations
- **Kraken API** - Price data, market depth
- **CoinGecko API** - Multi-coin prices, market data
- **Coinbase API** - Price data
- **Hyperliquid DEX** - Funding rates, derivatives data
- **Binance API** - Order book depth

### Service Dependencies
- **SQLite** - Local database (no external service)
- **None for production** - Fully self-contained application

## Configuration Dependencies

### Environment Variables
```
odin.config
  ├── ODIN_ENV (development/production)
  ├── ODIN_HOST (server bind address)
  ├── ODIN_PORT (server port)
  ├── DATABASE_URL (SQLite path)
  ├── EXCHANGE_API_KEY (exchange integration)
  ├── EXCHANGE_SECRET_KEY (exchange auth)
  └── JWT_SECRET_KEY (authentication)
```

## Testing Dependencies

### Test Dependency Graph
```
pytest
  ├── tests/unit/
  │    ├── test_strategies.py  → odin.strategies.*
  │    ├── test_database.py    → odin.core.database
  │    └── test_api.py         → odin.api.routes.*
  ├── tests/integration/
  │    └── test_full_system.py → All core modules
  └── conftest.py (fixtures)
       └── Creates test database, mocks
```

## Module Coupling Analysis

### Highly Coupled (Expected)
- `trading_engine` ↔ `portfolio_manager` - Business logic coupling
- `api.routes.*` ↔ `core.*` - API layer to business layer
- `strategies.*` ↔ `database` - Strategies need historical data

### Loosely Coupled (Good)
- `utils.*` - Independent utility functions
- `models.*` - Pure data structures
- `strategies.*` - Strategies don't depend on each other

### Decoupled (Excellent)
- `web/` - Frontend completely separate from backend
- `tests/` - Test isolation from production code
- `cache.py` - Optional caching layer

## Performance Considerations

### Module Load Time
1. **Fast** (<50ms): models, utils, database
2. **Medium** (50-200ms): strategies, core logic
3. **Slow** (>200ms): api.app (loads everything)

### Runtime Dependencies
- **Hot path**: `data_collector`, `cache`, `database`
- **Warm path**: `strategies`, `trading_engine`
- **Cold path**: `api.routes.*` (user-initiated)

## Future Dependency Improvements

### Recommended
1. **Add Redis** - External caching for multi-instance deployments
2. **Add PostgreSQL** - Production database with better concurrency
3. **Add Celery** - Background task processing
4. **Add Prometheus** - Metrics collection
5. **Add Sentry** - Error tracking

### Avoid
1. Heavy ML libraries in main process (use separate service)
2. Synchronous DB libraries (keep async)
3. Monolithic frameworks (keep FastAPI's modularity)

---

**Last Updated:** December 2024
**Odin Version:** 3.0+
