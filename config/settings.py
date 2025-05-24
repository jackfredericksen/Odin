# Bitcoin Trading Bot Configuration

# API Settings
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
DATA_UPDATE_INTERVAL = 30  # seconds between data collection
API_SERVER_PORT = 5000
API_SERVER_HOST = "0.0.0.0"

# Database Settings
DATABASE_PATH = "data/bitcoin_data.db"

# Trading Settings
INITIAL_BALANCE = 10000.0  # USD for paper trading
DEFAULT_TRADE_AMOUNT = 100.0  # USD per trade
MAX_PORTFOLIO_RISK = 0.02  # 2% max risk per trade

# Strategy Settings
MOVING_AVERAGE_SHORT = 5   # Short-term MA period
MOVING_AVERAGE_LONG = 20   # Long-term MA period
RSI_PERIOD = 14           # RSI calculation period
RSI_OVERSOLD = 30         # RSI oversold threshold
RSI_OVERBOUGHT = 70       # RSI overbought threshold

# Risk Management
STOP_LOSS_PERCENT = 0.05   # 5% stop loss
TAKE_PROFIT_PERCENT = 0.10 # 10% take profit

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/trading_bot.log"