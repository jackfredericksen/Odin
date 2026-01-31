"""
Cryptocurrency data endpoints - REAL DATA ONLY
Uses Kraken, CoinGecko, Coinbase, and other APIs for live crypto data.
Supports: BTC, ETH, SOL, XRP, BNB, SUI, HYPE
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import aiohttp
from fastapi import APIRouter, HTTPException, Query, Response, status

from odin.utils.cache import CACHE_PRESETS, cached
from odin.utils.logging import (
    LogContext,
    get_logger,
    log_operation_error,
    log_operation_start,
    log_operation_success,
)

logger = get_logger(__name__)
router = APIRouter()

# =============================================================================
# ASSET MAPPINGS - Crypto, Precious Metals, and Stocks
# =============================================================================

# Cryptocurrency mappings
COIN_MAPPINGS = {
    "BTC": {
        "name": "Bitcoin",
        "category": "crypto",
        "kraken": "XBTUSD",
        "binance": "BTCUSDT",
        "coingecko": "bitcoin",
        "coinbase": "BTC-USD",
        "hyperliquid": "BTC",
        "tradingview": "BINANCE:BTCUSDT",
        "circulating_supply": 19700000,
    },
    "ETH": {
        "name": "Ethereum",
        "category": "crypto",
        "kraken": "ETHUSD",
        "binance": "ETHUSDT",
        "coingecko": "ethereum",
        "coinbase": "ETH-USD",
        "hyperliquid": "ETH",
        "tradingview": "BINANCE:ETHUSDT",
        "circulating_supply": 120000000,
    },
    "SOL": {
        "name": "Solana",
        "category": "crypto",
        "kraken": "SOLUSD",
        "binance": "SOLUSDT",
        "coingecko": "solana",
        "coinbase": "SOL-USD",
        "hyperliquid": "SOL",
        "tradingview": "BINANCE:SOLUSDT",
        "circulating_supply": 580000000,
    },
    "XRP": {
        "name": "Ripple",
        "category": "crypto",
        "kraken": "XRPUSD",
        "binance": "XRPUSDT",
        "coingecko": "ripple",
        "coinbase": "XRP-USD",
        "hyperliquid": "XRP",
        "tradingview": "BINANCE:XRPUSDT",
        "circulating_supply": 57000000000,
    },
    "BNB": {
        "name": "BNB",
        "category": "crypto",
        "kraken": "BNBUSD",
        "binance": "BNBUSDT",
        "coingecko": "binancecoin",
        "coinbase": "BNB-USD",
        "hyperliquid": "BNB",
        "tradingview": "BINANCE:BNBUSDT",
        "circulating_supply": 144000000,
    },
    "SUI": {
        "name": "Sui",
        "category": "crypto",
        "kraken": "SUIUSD",
        "binance": "SUIUSDT",
        "coingecko": "sui",
        "coinbase": "SUI-USD",
        "hyperliquid": "SUI",
        "tradingview": "BINANCE:SUIUSDT",
        "circulating_supply": 2700000000,
    },
    "HYPE": {
        "name": "Hyperliquid",
        "category": "crypto",
        "kraken": "HYPEUSD",
        "binance": "HYPEUSDT",
        "coingecko": "hyperliquid",
        "coinbase": "HYPE-USD",
        "hyperliquid": "HYPE",
        "tradingview": "BYBIT:HYPEUSDT",
        "circulating_supply": 1000000000,
    },
}

# Precious Metals mappings (Yahoo Finance symbols)
METALS_MAPPINGS = {
    "GOLD": {
        "name": "Gold",
        "category": "metal",
        "yahoo": "GC=F",
        "tradingview": "COMEX:GC1!",
        "unit": "oz",
        "currency": "USD",
    },
    "SILVER": {
        "name": "Silver",
        "category": "metal",
        "yahoo": "SI=F",
        "tradingview": "COMEX:SI1!",
        "unit": "oz",
        "currency": "USD",
    },
    "PLATINUM": {
        "name": "Platinum",
        "category": "metal",
        "yahoo": "PL=F",
        "tradingview": "NYMEX:PL1!",
        "unit": "oz",
        "currency": "USD",
    },
    "PALLADIUM": {
        "name": "Palladium",
        "category": "metal",
        "yahoo": "PA=F",
        "tradingview": "NYMEX:PA1!",
        "unit": "oz",
        "currency": "USD",
    },
    "COPPER": {
        "name": "Copper",
        "category": "metal",
        "yahoo": "HG=F",
        "tradingview": "COMEX:HG1!",
        "unit": "lb",
        "currency": "USD",
    },
}

# Stock mappings (Yahoo Finance symbols)
STOCKS_MAPPINGS = {
    "SPY": {
        "name": "S&P 500 ETF",
        "category": "stock",
        "yahoo": "SPY",
        "tradingview": "AMEX:SPY",
        "sector": "Index ETF",
    },
    "QQQ": {
        "name": "Nasdaq 100 ETF",
        "category": "stock",
        "yahoo": "QQQ",
        "tradingview": "NASDAQ:QQQ",
        "sector": "Index ETF",
    },
    "AAPL": {
        "name": "Apple",
        "category": "stock",
        "yahoo": "AAPL",
        "tradingview": "NASDAQ:AAPL",
        "sector": "Technology",
    },
    "MSFT": {
        "name": "Microsoft",
        "category": "stock",
        "yahoo": "MSFT",
        "tradingview": "NASDAQ:MSFT",
        "sector": "Technology",
    },
    "GOOGL": {
        "name": "Alphabet",
        "category": "stock",
        "yahoo": "GOOGL",
        "tradingview": "NASDAQ:GOOGL",
        "sector": "Technology",
    },
    "AMZN": {
        "name": "Amazon",
        "category": "stock",
        "yahoo": "AMZN",
        "tradingview": "NASDAQ:AMZN",
        "sector": "Consumer",
    },
    "NVDA": {
        "name": "NVIDIA",
        "category": "stock",
        "yahoo": "NVDA",
        "tradingview": "NASDAQ:NVDA",
        "sector": "Technology",
    },
    "TSLA": {
        "name": "Tesla",
        "category": "stock",
        "yahoo": "TSLA",
        "tradingview": "NASDAQ:TSLA",
        "sector": "Automotive",
    },
    "META": {
        "name": "Meta",
        "category": "stock",
        "yahoo": "META",
        "tradingview": "NASDAQ:META",
        "sector": "Technology",
    },
    "COIN": {
        "name": "Coinbase",
        "category": "stock",
        "yahoo": "COIN",
        "tradingview": "NASDAQ:COIN",
        "sector": "Crypto",
    },
    "MSTR": {
        "name": "MicroStrategy",
        "category": "stock",
        "yahoo": "MSTR",
        "tradingview": "NASDAQ:MSTR",
        "sector": "Crypto",
    },
}

# Combined asset mappings for unified access
ALL_ASSETS = {**COIN_MAPPINGS, **METALS_MAPPINGS, **STOCKS_MAPPINGS}

def get_asset_category(symbol: str) -> str:
    """Get the category of an asset (crypto, metal, stock)"""
    symbol = symbol.upper()
    if symbol in COIN_MAPPINGS:
        return "crypto"
    elif symbol in METALS_MAPPINGS:
        return "metal"
    elif symbol in STOCKS_MAPPINGS:
        return "stock"
    return None


@cached(ttl=CACHE_PRESETS["realtime"], key_prefix="kraken_price")
async def fetch_kraken_price(symbol: str = "BTC") -> Dict[str, Any]:
    """Fetch real cryptocurrency price from Kraken API."""
    try:
        coin_config = COIN_MAPPINGS.get(symbol.upper())
        if not coin_config:
            return None

        kraken_pair = coin_config["kraken"]
        circulating_supply = coin_config["circulating_supply"]

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.kraken.com/0/public/Ticker",
                params={"pair": kraken_pair},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("error") and len(data["error"]) > 0:
                        return None

                    result = data.get("result", {})
                    # Kraken may return the pair with X prefix (e.g., XXBTZUSD or XBTUSD)
                    pair_data = None
                    for key in result.keys():
                        if kraken_pair.replace("X", "") in key or kraken_pair in key:
                            pair_data = result[key]
                            break

                    if not pair_data:
                        return None

                    last_price = float(pair_data.get("c", [0, 0])[0])
                    volume_24h = float(pair_data.get("v", [0, 0])[1])
                    bid_price = float(pair_data.get("b", [0, 0, 0])[0])
                    ask_price = float(pair_data.get("a", [0, 0, 0])[0])
                    high_24h = float(pair_data.get("h", [0, 0])[1])
                    low_24h = float(pair_data.get("l", [0, 0])[1])
                    open_price = float(pair_data.get("o", 0))

                    # Calculate 24h change
                    change_24h = (
                        ((last_price - open_price) / open_price * 100)
                        if open_price > 0
                        else 0
                    )
                    change_24h_abs = last_price - open_price

                    return {
                        "price": round(last_price, 2),
                        "change_24h": round(change_24h, 2),
                        "change_24h_abs": round(change_24h_abs, 2),
                        "high_24h": round(high_24h, 2),
                        "low_24h": round(low_24h, 2),
                        "volume": round(volume_24h, 2),
                        "volume_24h": round(volume_24h, 2),
                        "bid": round(bid_price, 2),
                        "ask": round(ask_price, 2),
                        "market_cap": round(last_price * circulating_supply, 0),
                        "timestamp": datetime.now(timezone.utc).timestamp(),
                        "last_updated": datetime.now(timezone.utc).timestamp(),
                        "source": "kraken",
                        "symbol": f"{symbol.upper()}-USD",
                        "currency": "USD",
                    }
    except Exception as e:
        logger.error(
            f"Kraken API error for {symbol}",
            context=LogContext(
                component="data_api",
                operation="fetch_kraken_price",
                additional_data={"symbol": symbol, "error": str(e)},
            ),
        )
        return None


@cached(ttl=CACHE_PRESETS["realtime"], key_prefix="coingecko_price")
async def fetch_coingecko_price(symbol: str = "BTC") -> Dict[str, Any]:
    """Fetch real cryptocurrency price from CoinGecko API."""
    try:
        coin_config = COIN_MAPPINGS.get(symbol.upper())
        if not coin_config:
            return None

        coingecko_id = coin_config["coingecko"]
        circulating_supply = coin_config["circulating_supply"]

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": coingecko_id,
                    "vs_currencies": "usd",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                    "include_market_cap": "true",
                },
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    coin_data = data.get(coingecko_id, {})

                    price = float(coin_data.get("usd", 0))
                    change_24h = float(coin_data.get("usd_24h_change", 0))
                    volume_24h = (
                        float(coin_data.get("usd_24h_vol", 0)) / 1e9
                    )  # Convert to billions

                    # Estimate high/low based on price and change
                    high_24h = (
                        price if change_24h >= 0 else price / (1 + change_24h / 100)
                    )
                    low_24h = (
                        price if change_24h <= 0 else price / (1 + change_24h / 100)
                    )

                    return {
                        "price": round(price, 2),
                        "change_24h": round(change_24h, 2),
                        "change_24h_abs": round(price * change_24h / 100, 2),
                        "high_24h": round(high_24h, 2),
                        "low_24h": round(low_24h, 2),
                        "volume": round(volume_24h, 2),
                        "volume_24h": round(volume_24h, 2),
                        "market_cap": round(
                            float(coin_data.get("usd_market_cap", 0)), 0
                        ),
                        "timestamp": datetime.now(timezone.utc).timestamp(),
                        "last_updated": datetime.now(timezone.utc).timestamp(),
                        "source": "coingecko",
                        "symbol": f"{symbol.upper()}-USD",
                        "currency": "USD",
                    }
    except Exception as e:
        logger.error(
            f"CoinGecko API error for {symbol}",
            context=LogContext(
                component="data_api",
                operation="fetch_coingecko_price",
                additional_data={"symbol": symbol, "error": str(e)},
            ),
        )
        return None


@cached(ttl=CACHE_PRESETS["realtime"], key_prefix="coinbase_price")
async def fetch_coinbase_price(symbol: str = "BTC") -> Dict[str, Any]:
    """Fetch real cryptocurrency price from Coinbase API."""
    try:
        coin_config = COIN_MAPPINGS.get(symbol.upper())
        if not coin_config:
            return None

        coinbase_pair = coin_config["coinbase"]
        circulating_supply = coin_config["circulating_supply"]

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.coinbase.com/v2/prices/{coinbase_pair}/spot",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    price_data = data.get("data", {})
                    price = float(price_data.get("amount", 0))

                    return {
                        "price": round(price, 2),
                        "market_cap": round(price * circulating_supply, 0),
                        "timestamp": datetime.now(timezone.utc).timestamp(),
                        "last_updated": datetime.now(timezone.utc).timestamp(),
                        "source": "coinbase",
                        "symbol": f"{symbol.upper()}-USD",
                        "currency": "USD",
                    }
    except Exception as e:
        logger.error(
            f"Coinbase API error for {symbol}",
            context=LogContext(
                component="data_api",
                operation="fetch_coinbase_price",
                additional_data={"symbol": symbol, "error": str(e)},
            ),
        )
        return None


@cached(ttl=CACHE_PRESETS["realtime"], key_prefix="hyperliquid_price")
async def fetch_hyperliquid_price(symbol: str = "BTC") -> Dict[str, Any]:
    """Fetch real cryptocurrency price and funding rate from Hyperliquid DEX."""
    try:
        coin_config = COIN_MAPPINGS.get(symbol.upper())
        if not coin_config:
            return None

        hyperliquid_symbol = coin_config["hyperliquid"]
        circulating_supply = coin_config["circulating_supply"]

        async with aiohttp.ClientSession() as session:
            # Get meta and asset contexts (includes funding, OI, volume)
            async with session.post(
                "https://api.hyperliquid.xyz/info",
                json={"type": "metaAndAssetCtxs"},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    # data[0] = meta (universe info with coin names)
                    # data[1] = asset contexts (price, funding, etc)

                    meta = data[0]
                    contexts = data[1]

                    # Find the index for the requested coin
                    coin_index = None
                    for idx, coin_meta in enumerate(meta.get("universe", [])):
                        if coin_meta.get("name") == hyperliquid_symbol:
                            coin_index = idx
                            break

                    if coin_index is None or coin_index >= len(contexts):
                        return None

                    coin_ctx = contexts[coin_index]
                    if not coin_ctx:
                        return None

                    mark_price = float(coin_ctx.get("markPx", 0))
                    prev_day_px = float(coin_ctx.get("prevDayPx", mark_price))
                    funding_rate = float(coin_ctx.get("funding", 0))
                    open_interest = float(coin_ctx.get("openInterest", 0))
                    volume_24h = float(coin_ctx.get("dayNtlVlm", 0))

                    # Calculate 24h change
                    change_24h = (
                        ((mark_price - prev_day_px) / prev_day_px * 100)
                        if prev_day_px > 0
                        else 0
                    )
                    change_24h_abs = mark_price - prev_day_px

                    # Estimate high/low (Hyperliquid doesn't provide these directly)
                    high_24h = (
                        mark_price * 1.015 if change_24h >= 0 else prev_day_px * 1.01
                    )
                    low_24h = (
                        mark_price * 0.985 if change_24h <= 0 else prev_day_px * 0.99
                    )

                    return {
                        "price": round(mark_price, 2),
                        "change_24h": round(change_24h, 2),
                        "change_24h_abs": round(change_24h_abs, 2),
                        "high_24h": round(high_24h, 2),
                        "low_24h": round(low_24h, 2),
                        "volume": round(
                            open_interest, 2
                        ),  # Open Interest in coin units
                        "volume_24h": round(
                            volume_24h / 1e9, 2
                        ),  # Convert to billions USD
                        "market_cap": round(mark_price * circulating_supply, 0),
                        "timestamp": datetime.now(timezone.utc).timestamp(),
                        "last_updated": datetime.now(timezone.utc).timestamp(),
                        "source": "hyperliquid",
                        "symbol": f"{symbol.upper()}-USD",
                        "currency": "USD",
                        "funding_rate": round(
                            funding_rate * 100, 4
                        ),  # Convert to percentage
                        "open_interest": round(open_interest, 2),
                    }
    except Exception as e:
        logger.error(
            f"Hyperliquid API error for {symbol}",
            context=LogContext(
                component="data_api",
                operation="fetch_hyperliquid_price",
                additional_data={"symbol": symbol, "error": str(e)},
            ),
        )
        return None


# =============================================================================
# Yahoo Finance Fetcher for Metals and Stocks
# =============================================================================

@cached(ttl=CACHE_PRESETS["short"], key_prefix="yahoo_price")
async def fetch_yahoo_price(symbol: str) -> Dict[str, Any]:
    """
    Fetch price data from Yahoo Finance for metals and stocks.
    Uses the Yahoo Finance v8 quote endpoint.
    """
    try:
        symbol_upper = symbol.upper()

        # Get Yahoo symbol from our mappings
        yahoo_symbol = None
        asset_name = None
        asset_category = None

        if symbol_upper in METALS_MAPPINGS:
            yahoo_symbol = METALS_MAPPINGS[symbol_upper]["yahoo"]
            asset_name = METALS_MAPPINGS[symbol_upper]["name"]
            asset_category = "metal"
        elif symbol_upper in STOCKS_MAPPINGS:
            yahoo_symbol = STOCKS_MAPPINGS[symbol_upper]["yahoo"]
            asset_name = STOCKS_MAPPINGS[symbol_upper]["name"]
            asset_category = "stock"
        else:
            return None

        async with aiohttp.ClientSession() as session:
            # Yahoo Finance v8 quote API
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
            params = {
                "interval": "1d",
                "range": "5d",
                "includePrePost": "false"
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    chart = data.get("chart", {})
                    result = chart.get("result", [])

                    if not result:
                        return None

                    quote_data = result[0]
                    meta = quote_data.get("meta", {})
                    indicators = quote_data.get("indicators", {})
                    quote = indicators.get("quote", [{}])[0]

                    # Get current price
                    price = meta.get("regularMarketPrice", 0)
                    prev_close = meta.get("previousClose", price)
                    day_high = meta.get("regularMarketDayHigh", price)
                    day_low = meta.get("regularMarketDayLow", price)
                    volume = meta.get("regularMarketVolume", 0)

                    # Calculate change
                    change_abs = price - prev_close
                    change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0

                    # Get historical highs/lows from quote data
                    highs = quote.get("high", [])
                    lows = quote.get("low", [])
                    high_24h = max(highs) if highs else day_high
                    low_24h = min(lows) if lows else day_low

                    return {
                        "price": round(price, 2),
                        "change_24h": round(change_pct, 2),
                        "change_24h_abs": round(change_abs, 2),
                        "high_24h": round(high_24h, 2) if high_24h else round(price, 2),
                        "low_24h": round(low_24h, 2) if low_24h else round(price, 2),
                        "volume": volume,
                        "volume_24h": volume,
                        "prev_close": round(prev_close, 2),
                        "timestamp": datetime.now(timezone.utc).timestamp(),
                        "last_updated": datetime.now(timezone.utc).timestamp(),
                        "source": "yahoo",
                        "symbol": symbol_upper,
                        "name": asset_name,
                        "category": asset_category,
                        "currency": "USD",
                    }

    except Exception as e:
        logger.error(f"Yahoo Finance API error for {symbol}: {e}")
        return None


@router.get("/current", response_model=Dict[str, Any])
async def get_current_price(
    symbol: str = Query(
        default="BTC",
        description="Asset symbol (crypto, metal, or stock)",
    )
):
    """Get current price for crypto, precious metals, or stocks."""
    try:
        symbol = symbol.upper()

        # Determine asset category
        category = get_asset_category(symbol)

        if category is None:
            supported_crypto = ", ".join(COIN_MAPPINGS.keys())
            supported_metals = ", ".join(METALS_MAPPINGS.keys())
            supported_stocks = ", ".join(STOCKS_MAPPINGS.keys())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported asset: {symbol}. Supported - Crypto: {supported_crypto} | Metals: {supported_metals} | Stocks: {supported_stocks}",
            )

        # Handle metals and stocks via Yahoo Finance
        if category in ("metal", "stock"):
            asset_config = METALS_MAPPINGS.get(symbol) or STOCKS_MAPPINGS.get(symbol)
            asset_name = asset_config["name"]

            yahoo_data = await fetch_yahoo_price(symbol)
            if yahoo_data and yahoo_data.get("price", 0) > 0:
                return {
                    "success": True,
                    "message": f"{asset_name} data retrieved successfully",
                    "data": yahoo_data,
                    "error": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Unable to fetch {asset_name} data. Market may be closed.",
                )

        # Handle crypto (existing logic)
        if symbol not in COIN_MAPPINGS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported cryptocurrency: {symbol}. Supported: {', '.join(COIN_MAPPINGS.keys())}",
            )

        coin_name = COIN_MAPPINGS[symbol]["name"]

        # Try Kraken first (most complete data, includes bid/ask)
        kraken_data = await fetch_kraken_price(symbol)
        if kraken_data and kraken_data.get("price", 0) > 0:
            return {
                "success": True,
                "message": f"{coin_name} data retrieved successfully",
                "data": kraken_data,
                "error": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Try Hyperliquid (includes funding rate and open interest)
        hyperliquid_data = await fetch_hyperliquid_price(symbol)
        if hyperliquid_data and hyperliquid_data.get("price", 0) > 0:
            return {
                "success": True,
                "message": f"{coin_name} data retrieved successfully (with funding rate)",
                "data": hyperliquid_data,
                "error": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Fallback to CoinGecko
        coingecko_data = await fetch_coingecko_price(symbol)
        if coingecko_data and coingecko_data.get("price", 0) > 0:
            return {
                "success": True,
                "message": f"{coin_name} data retrieved successfully",
                "data": coingecko_data,
                "error": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Last fallback to Coinbase
        coinbase_data = await fetch_coinbase_price(symbol)
        if coinbase_data and coinbase_data.get("price", 0) > 0:
            # Supplement Coinbase data with estimated values
            price = coinbase_data["price"]
            coinbase_data.update(
                {
                    "change_24h": 0.0,
                    "change_24h_abs": 0.0,
                    "high_24h": round(price * 1.02, 2),
                    "low_24h": round(price * 0.98, 2),
                    "volume": 0.0,
                    "volume_24h": 0.0,
                }
            )
            return {
                "success": True,
                "message": f"{coin_name} data retrieved successfully (limited data)",
                "data": coinbase_data,
                "error": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # All sources failed
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"All data sources are currently unavailable for {coin_name}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch current {symbol} price: {str(e)}",
        )


@router.get("/price", response_model=Dict[str, Any])
async def get_coin_price(
    symbol: str = Query(
        default="BTC",
        description="Asset symbol (crypto, metal, or stock)",
    )
):
    """Alias for /current endpoint - Get current asset price."""
    return await get_current_price(symbol=symbol)


@router.get("/assets", response_model=Dict[str, Any])
async def get_available_assets():
    """Get list of all available assets organized by category."""
    return {
        "success": True,
        "data": {
            "crypto": {
                symbol: {
                    "name": config["name"],
                    "tradingview": config.get("tradingview", ""),
                }
                for symbol, config in COIN_MAPPINGS.items()
            },
            "metals": {
                symbol: {
                    "name": config["name"],
                    "tradingview": config.get("tradingview", ""),
                    "unit": config.get("unit", "oz"),
                }
                for symbol, config in METALS_MAPPINGS.items()
            },
            "stocks": {
                symbol: {
                    "name": config["name"],
                    "tradingview": config.get("tradingview", ""),
                    "sector": config.get("sector", ""),
                }
                for symbol, config in STOCKS_MAPPINGS.items()
            },
        },
        "counts": {
            "crypto": len(COIN_MAPPINGS),
            "metals": len(METALS_MAPPINGS),
            "stocks": len(STOCKS_MAPPINGS),
            "total": len(ALL_ASSETS),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@cached(ttl=CACHE_PRESETS["history"], key_prefix="kraken_history")
async def fetch_kraken_history(symbol: str, hours: int) -> Dict[str, Any]:
    """Fetch historical data from Kraken with caching."""
    coin_config = COIN_MAPPINGS[symbol]
    kraken_pair = coin_config["kraken"]

    # Determine interval based on hours requested
    if hours <= 24:
        interval = 60  # 1 hour candles
    elif hours <= 168:  # 7 days
        interval = 240  # 4 hour candles
    else:
        interval = 1440  # 1 day candles

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.kraken.com/0/public/OHLC",
            params={"pair": kraken_pair, "interval": interval},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            if response.status != 200:
                return None

            data = await response.json()

            if data.get("error") and len(data["error"]) > 0:
                return None

            result = data.get("result", {})
            ohlc_data = None
            for key in result.keys():
                if key != "last":
                    ohlc_data = result[key]
                    break

            if not ohlc_data:
                ohlc_data = []

            # Convert to format expected by frontend
            history = []
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            for candle in ohlc_data:
                timestamp = int(candle[0])
                candle_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)

                if candle_time >= cutoff_time:
                    history.append({
                        "timestamp": timestamp,
                        "price": float(candle[4]),
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "volume": float(candle[6]),
                    })

            return {
                "history": history,
                "hours": hours,
                "interval_minutes": interval,
                "source": "kraken",
            }


@router.get("/history/{hours}", response_model=Dict[str, Any])
async def get_price_history(
    hours: int,
    symbol: str = Query(default="BTC", description="Cryptocurrency symbol")
):
    """Get historical cryptocurrency price data from Kraken."""
    if hours < 1 or hours > 720:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hours must be between 1 and 720 (30 days)",
        )

    symbol = symbol.upper()
    if symbol not in COIN_MAPPINGS:
        supported = ", ".join(COIN_MAPPINGS.keys())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported cryptocurrency: {symbol}. Supported: {supported}",
        )

    try:
        data = await fetch_kraken_history(symbol, hours)
        if data is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Kraken API unavailable",
            )

        return {
            "success": True,
            "message": f"Retrieved {len(data['history'])} data points",
            "data": data,
            "error": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch price history: {str(e)}",
        )


@router.get("/analytics/{symbol}", response_model=Dict[str, Any])
@cached(ttl=300)
async def get_analytics(
    symbol: str,
    hours: int = Query(default=168, description="Hours of data for analysis"),
):
    """Get comprehensive technical analysis indicators."""
    try:
        history_data = await get_price_history(hours=hours, symbol=symbol)
        
        if not history_data.get("success"):
            raise HTTPException(status_code=500, detail="Failed to fetch price history")
        
        history = history_data["data"]["history"]
        
        if len(history) < 26:
            raise HTTPException(status_code=400, detail="Insufficient data")
        
        prices = [h["price"] for h in history]
        current_price = prices[-1]
        
        # Calculate RSI
        rsi = _calc_rsi(prices, 14)
        
        # Calculate MACD
        ema12 = _calc_ema(prices, 12)
        ema26 = _calc_ema(prices, 26)
        macd = ema12 - ema26
        signal = macd * 0.9
        histogram = macd - signal
        
        # Calculate SMA
        sma20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else current_price
        sma50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else current_price
        
        # Calculate Bollinger Bands
        std = (sum((p - sma20)**2 for p in prices[-20:]) / 20) ** 0.5 if len(prices) >= 20 else 0
        bb_upper = sma20 + (2 * std)
        bb_lower = sma20 - (2 * std)
        
        # Stochastic
        recent = prices[-14:] if len(prices) >= 14 else prices
        high = max(recent)
        low = min(recent)
        stoch_k = ((current_price - low) / (high - low) * 100) if high != low else 50
        
        # ATR
        ranges = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
        atr = sum(ranges[-14:]) / 14 if len(ranges) >= 14 else 0
        
        # Generate signals
        signals = {
            "rsi": "BUY" if rsi < 30 else "SELL" if rsi > 70 else "HOLD",
            "macd": "BUY" if histogram > 0 else "SELL",
            "ma": "BUY" if ema12 > ema26 else "SELL",
            "bb": "BUY" if current_price < bb_lower else "SELL" if current_price > bb_upper else "HOLD"
        }
        
        buy_count = sum(1 for s in signals.values() if s == "BUY")
        sell_count = sum(1 for s in signals.values() if s == "SELL")
        total = len(signals)
        buy_pct = (buy_count / total) * 100
        
        overall = "STRONG BUY" if buy_pct >= 75 else "BUY" if buy_pct >= 50 else "SELL" if buy_pct <= 25 else "HOLD"
        
        return {
            "success": True,
            "symbol": symbol,
            "current_price": current_price,
            "indicators": {
                "rsi": {"value": round(rsi, 2), "signal": signals["rsi"]},
                "macd": {"value": round(macd, 2), "histogram": round(histogram, 2), "signal": signals["macd"]},
                "ma": {"sma20": round(sma20, 2), "ema12": round(ema12, 2), "ema26": round(ema26, 2), "signal": signals["ma"]},
                "bb": {"upper": round(bb_upper, 2), "middle": round(sma20, 2), "lower": round(bb_lower, 2), "signal": signals["bb"]},
                "stoch": {"k": round(stoch_k, 2)},
                "atr": {"value": round(atr, 2)}
            },
            "signals": signals,
            "summary": {
                "overall_signal": overall,
                "buy_signals": buy_count,
                "sell_signals": sell_count,
                "buy_percentage": round(buy_pct, 1),
                "confidence": round(max(buy_pct, 100 - buy_pct), 1)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Analytics error for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _calc_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [c if c > 0 else 0 for c in changes]
    losses = [-c if c < 0 else 0 for c in changes]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _calc_ema(prices, period):
    if len(prices) < period:
        return sum(prices) / len(prices)
    mult = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for p in prices[period:]:
        ema = (p * mult) + (ema * (1 - mult))
    return ema
